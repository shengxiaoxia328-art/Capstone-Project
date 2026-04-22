"""
单模型评测脚本
对指定模型在整个测评集上进行完整评分
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import dotenv_values

# 项目根路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEMO_DIR = PROJECT_ROOT / "demo"
SIMULATION_DIR = PROJECT_ROOT / "simulation"
CONFIG_DIR = SIMULATION_DIR / "config"
EVALUATION_DIR = SIMULATION_DIR / "evaluation"
DEFAULT_SAMPLES_FILE = CONFIG_DIR / "test_samples.json"


class SingleModelEvaluator:
    """单个模型的完整评测器"""

    def __init__(self, model_name: str, config_file: str = "models.yaml", sample_id: str = "", samples_file: str = "", verbose: bool = False, retry_failed: bool = False, output_tag: str = ""):
        self.model_name = model_name
        self.config_file = config_file
        self.verbose = verbose
        self.samples_file = samples_file
        self.retry_failed = retry_failed
        self.output_tag = output_tag
        self.demo_env = dotenv_values(DEMO_DIR / ".env")
        self.config = self._load_config()
        self.model_config = self._load_model_config(model_name)
        self.eval_config = self.config.get("evaluation", {})
        self.weights = self._normalize_weights(
            float(self.eval_config.get("photo_weight", 0.3)),
            float(self.eval_config.get("story_weight", 0.5)),
            float(self.eval_config.get("interview_weight", 0.2)),
        )
        self.timeout_seconds = int(self.eval_config.get("timeout_seconds", 120))
        self.retries = int(self.eval_config.get("retries", 2))
        self.samples = self._load_samples(sample_id=sample_id, samples_file=samples_file)
        self.results = []
        dir_name = f"{model_name}_{output_tag}" if output_tag else model_name
        self.output_dir = EVALUATION_DIR / dir_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._existing_results = None
        self._merge_mode = False
        if self.retry_failed:
            self._filter_to_failed_only()
        elif sample_id:
            self._load_existing_for_merge()

    def _load_config(self) -> Dict[str, Any]:
        """加载模型配置"""
        config_path = CONFIG_DIR / self.config_file
        if not config_path.exists():
            raise FileNotFoundError(f"模型配置文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _load_model_config(self, model_name: str) -> Dict[str, Any]:
        models = self.config.get("models", {})
        if model_name not in models:
            raise KeyError(f"未在 models.yaml 中找到模型: {model_name}")

        model_config = models[model_name]
        if not model_config.get("enabled", False):
            raise ValueError(f"模型 {model_name} 在配置中未启用")
        return model_config

    def _read_text_file(self, file_path: str) -> str:
        if not file_path:
            return ""

        path = Path(file_path)
        if not path.is_absolute():
            path = (PROJECT_ROOT / path).resolve()
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def _normalize_mme_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for task in tasks or []:
            question = str(task.get("question") or task.get("q") or "").strip()
            answer = str(task.get("answer") or task.get("a") or "").strip()
            if question and answer:
                normalized.append({
                    "question": question,
                    "answer": answer,
                })
        return normalized

    def _normalize_mmbench_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for task in tasks or []:
            question = str(task.get("question") or task.get("q") or "").strip()
            options = task.get("options") or {}
            answer = str(task.get("answer") or task.get("a") or "").strip()
            if question and options and answer:
                normalized.append({
                    "question": question,
                    "options": options,
                    "answer": answer,
                })
        return normalized

    def _build_sample_id(self, raw_sample: Dict[str, Any], index: int) -> str:
        existing = str(raw_sample.get("sample_id") or "").strip()
        if existing:
            return existing

        image_path = str(raw_sample.get("image_path") or "").strip()
        if image_path:
            return Path(image_path).stem
        return f"sample_{index:03d}"

    def _normalize_sample(self, raw_sample: Dict[str, Any], index: int) -> Dict[str, Any]:
        memoir_text = str(raw_sample.get("memoir_text") or "").strip()
        if not memoir_text:
            memoir_text = self._read_text_file(str(raw_sample.get("memoir_path") or ""))

        interview_text = self._read_text_file(str(raw_sample.get("interview_path") or ""))
        reference_story = str(raw_sample.get("reference_story") or "").strip() or memoir_text

        return {
            "sample_id": self._build_sample_id(raw_sample, index),
            "image_path": str(raw_sample.get("image_path") or "").strip(),
            "image_description": str(raw_sample.get("image_description") or "").strip(),
            "memoir_text": memoir_text,
            "memoir_path": str(raw_sample.get("memoir_path") or "").strip(),
            "interview_path": str(raw_sample.get("interview_path") or "").strip(),
            "interview_text": interview_text,
            "mme_tasks": self._normalize_mme_tasks(raw_sample.get("mme_tasks") or []),
            "mmbench_tasks": self._normalize_mmbench_tasks(raw_sample.get("mmbench_tasks") or []),
            "hooks": raw_sample.get("hooks") or [],
            "reference_story": reference_story,
        }

    def _load_existing_for_merge(self):
        """加载已有结果文件，用于 --sample-id 增量合并。"""
        results_file = self.output_dir / f"{self.model_name}_results.json"
        if not results_file.exists():
            return
        with open(results_file, "r", encoding="utf-8") as f:
            self._existing_results = json.load(f)
        self._merge_mode = True

    def _filter_to_failed_only(self):
        """只保留上次失败的样本，用于重跑。"""
        results_file = self.output_dir / f"{self.model_name}_results.json"
        if not results_file.exists():
            print(f"[warn] 未找到已有结果文件 {results_file}，将跑全量样本")
            return
        with open(results_file, "r", encoding="utf-8") as f:
            self._existing_results = json.load(f)
        failed_ids = set()
        for s in self._existing_results.get("samples", []):
            if "error" in s and s.get("photo_score", 0) == 0:
                failed_ids.add(s["sample_id"])
        if not failed_ids:
            print(f"模型 {self.model_name} 无失败样本，跳过")
            self.samples = []
            return
        self.samples = [s for s in self.samples if s["sample_id"] in failed_ids]
        print(f"找到 {len(failed_ids)} 个失败样本，准备重跑: {', '.join(failed_ids)}")

    def _load_samples(self, sample_id: str = "", samples_file: str = "") -> List[Dict[str, Any]]:
        """加载并归一化测评样本集。"""
        configured_path = Path(samples_file) if samples_file else DEFAULT_SAMPLES_FILE
        if not configured_path.is_absolute():
            configured_path = (PROJECT_ROOT / configured_path).resolve()

        if not configured_path.exists():
            raise FileNotFoundError(f"样本集文件不存在: {configured_path}")

        with open(configured_path, "r", encoding="utf-8-sig") as f:
            raw_samples = json.load(f)

        samples = [self._normalize_sample(sample, index + 1) for index, sample in enumerate(raw_samples)]

        if not sample_id:
            return samples

        filtered_samples = [sample for sample in samples if sample.get("sample_id") == sample_id]
        if not filtered_samples:
            raise ValueError(f"未找到 sample_id={sample_id} 的样本")
        return filtered_samples

    def _normalize_weights(self, photo_weight: float, story_weight: float, interview_weight: float) -> Dict[str, float]:
        total = photo_weight + story_weight + interview_weight
        if total <= 0:
            raise ValueError("photo/story/interview 权重之和必须大于 0")
        return {
            "photo": round(photo_weight / total, 4),
            "story": round(story_weight / total, 4),
            "interview": round(interview_weight / total, 4),
        }

    def _resolve_env_placeholder(self, value: str) -> str:
        if not isinstance(value, str):
            return str(value)

        match = re.fullmatch(r"\$\{([A-Z0-9_]+)\}", value.strip())
        if match:
            key = match.group(1)
            return os.environ.get(key, "") or str(self.demo_env.get(key, ""))
        return value

    def _build_model_environment(self) -> Dict[str, str]:
        """根据 models.yaml 构建当前模型的运行环境。"""
        env = os.environ.copy()
        provider = str(self.model_config.get("provider", "")).lower()
        endpoint = self._resolve_env_placeholder(str(self.model_config.get("endpoint", "")))
        api_key = self._resolve_env_placeholder(str(self.model_config.get("api_key", "")))
        text_model = self._resolve_env_placeholder(str(self.model_config.get("text_model", "")))
        vision_model = self._resolve_env_placeholder(str(self.model_config.get("vision_model", "")))

        for key in [
            "MODEL_PROVIDER",
            "MODEL_API_KEY",
            "MODEL_API_ENDPOINT",
            "MODEL_TEXT_MODEL",
            "MODEL_VISION_MODEL",
            "HUNYUAN_API_KEY",
            "HUNYUAN_API_ENDPOINT",
            "HUNYUAN_VISION_MODEL",
            "HUNYUAN_TEXT_MODEL",
            "GEMINI_API_KEY",
            "GEMINI_API_ENDPOINT",
            "GEMINI_MODEL_NAME",
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_API_ENDPOINT",
        ]:
            env.pop(key, None)

        env["MODEL_PROVIDER"] = provider
        env["MODEL_API_KEY"] = api_key
        env["MODEL_API_ENDPOINT"] = endpoint
        env["MODEL_TEXT_MODEL"] = text_model or vision_model
        env["MODEL_VISION_MODEL"] = vision_model or text_model

        if provider == "hunyuan":
            env["HUNYUAN_API_KEY"] = api_key
            env["HUNYUAN_API_ENDPOINT"] = endpoint
            env["HUNYUAN_VISION_MODEL"] = vision_model or text_model
            env["HUNYUAN_TEXT_MODEL"] = text_model or vision_model
        elif provider == "gemini":
            env["GEMINI_API_KEY"] = api_key
            env["GEMINI_API_ENDPOINT"] = endpoint
            env["GEMINI_MODEL_NAME"] = text_model or vision_model
        elif provider == "anthropic":
            env["ANTHROPIC_API_KEY"] = api_key
            env["ANTHROPIC_API_ENDPOINT"] = endpoint

        if not api_key:
            raise RuntimeError(f"模型 {self.model_name} 缺少 API key，请检查环境变量或 models.yaml")

        # 确保子进程使用 UTF-8
        env["PYTHONIOENCODING"] = "utf-8"

        return env

    def _run_generation_pipeline(self, sample: Dict[str, Any], env: Dict[str, str]) -> Dict[str, Any]:
        """运行真实的生成链路：图片分析 -> 问题生成 -> 故事生成。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            sample_file = tmpdir_path / "sample.json"
            with open(sample_file, "w", encoding="utf-8") as f:
                json.dump(sample, f, ensure_ascii=False, indent=2)

            cmd = [
                sys.executable,
                str(SIMULATION_DIR / "scripts" / "run_sample_pipeline.py"),
                "--sample-file", str(sample_file),
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_seconds,
                cwd=str(PROJECT_ROOT),
                env=env,
            )

            stdout_text = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
            stderr_text = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''

            if result.returncode != 0:
                raise RuntimeError(stderr_text.strip() or "run_sample_pipeline.py 执行失败")

            try:
                return json.loads(stdout_text)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"无法解析生成链路输出: {exc}\n输出内容: {stdout_text[:500]}") from exc

    def evaluate(self) -> Dict[str, Any]:
        """对所有样本进行评测"""
        print(f"\n{'='*60}")
        print(f"开始评测模型: {self.model_name}")
        print(f"样本数: {len(self.samples)}")
        print(f"{'='*60}\n")

        env = self._build_model_environment()

        for i, sample in enumerate(self.samples, 1):
            print(f"[{i}/{len(self.samples)}] 评测样本: {sample['sample_id']}...", end=" ", flush=True)
            try:
                result = self._evaluate_single_sample(sample)
                self.results.append(result)
                print("[OK] 完成", flush=True)
            except Exception as e:
                print(f"[FAIL] 失败: {str(e)}", flush=True)
                self.results.append({
                    "sample_id": sample["sample_id"],
                    "error": str(e),
                    "photo_score": 0,
                    "story_score": 0,
                    "interview_score": 0,
                    "final_score": 0,
                })

        return self._aggregate_results()

    def _merge_retry_results(self, new_results: List[Dict]) -> List[Dict]:
        """将新跑出的结果合并进上次的完整结果。"""
        if not self._existing_results:
            return new_results
        new_map = {r["sample_id"]: r for r in new_results}
        merged = []
        for s in self._existing_results["samples"]:
            sid = s["sample_id"]
            if sid in new_map:
                merged.append(new_map.pop(sid))
            else:
                merged.append(s)
        for leftover in new_map.values():
            merged.append(leftover)
        return merged

    def _evaluate_single_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """评测单个样本"""
        env = self._build_model_environment()
        generation_result = self._run_generation_pipeline(sample, env)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # 1. 准备临时 benchmark 文件
            benchmark_file = tmpdir_path / "benchmark.json"
            benchmark_data = {
                "image_path": sample.get("image_path", ""),
                "image_description": sample.get("image_description", ""),
                "mme_tasks": sample.get("mme_tasks", []),
                "mmbench_tasks": sample.get("mmbench_tasks", []),
                "hooks": sample.get("hooks", []),
            }
            with open(benchmark_file, "w", encoding="utf-8") as f:
                json.dump(benchmark_data, f, ensure_ascii=False, indent=2)

            # 2. 准备临时故事文件
            story_file = tmpdir_path / "story.txt"
            story_text = generation_result.get("story", "").strip()
            if not story_text:
                raise RuntimeError("生成链路未返回故事文本")
            with open(story_file, "w", encoding="utf-8") as f:
                f.write(story_text)

            qa_history = generation_result.get("qa_history", [])
            qa_history_file = None
            if qa_history:
                qa_history_file = tmpdir_path / "qa_history.json"
                with open(qa_history_file, "w", encoding="utf-8") as f:
                    json.dump(qa_history, f, ensure_ascii=False, indent=2)

            # 3. 准备参考故事文件（可选）
            reference_file = None
            if sample.get("reference_story"):
                reference_file = tmpdir_path / "reference.txt"
                with open(reference_file, "w", encoding="utf-8") as f:
                    f.write(sample["reference_story"])

            # 4. 获取实际图片路径
            image_path = sample.get("image_path", "")
            if not Path(image_path).is_absolute():
                image_path = str(PROJECT_ROOT / image_path)

            # 5. 调用 judge_final.py 进行评分
            cmd = [
                sys.executable,
                str(DEMO_DIR / "judge_final.py"),
                "--benchmark-file", str(benchmark_file),
                "--story-file", str(story_file),
                "--photo-weight", str(self.weights["photo"]),
                "--story-weight", str(self.weights["story"]),
                "--interview-weight", str(self.weights["interview"]),
                "--image-root", str(PROJECT_ROOT),
            ]

            if self.weights["interview"] > 0:
                if not qa_history_file:
                    raise RuntimeError("interview_weight > 0，但生成链路未产生 qa_history")
                cmd.extend(["--qa-history-file", str(qa_history_file)])
            
            if reference_file:
                cmd.extend(["--reference-file", str(reference_file)])

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_seconds,
                cwd=str(DEMO_DIR),
                env=env,
            )

            stdout_text = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
            stderr_text = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''

            if result.returncode != 0:
                raise RuntimeError(f"judge_final.py 执行失败: {stderr_text}")

            # 6. 解析输出
            try:
                eval_result = json.loads(stdout_text)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"无法解析 judge_final.py 输出: {e}\n输出内容: {stdout_text[:500]}")

            # 7. 提取关键指标
            return {
                "sample_id": sample["sample_id"],
                "photo_score": eval_result.get("photo_evaluation", {}).get("normalized_score", 0),
                "story_score": eval_result.get("story_evaluation", {}).get("final_score", 0),
                "interview_score": eval_result.get("interview_evaluation", {}).get("final_score", 0) if eval_result.get("interview_evaluation") else 0,
                "final_score": eval_result.get("final_score", 0),
                "generated_story": story_text,
                "qa_history": qa_history,
                "analysis_result": generation_result.get("analysis_result", {}),
                "details": eval_result,
            }

    def _aggregate_results(self) -> Dict[str, Any]:
        """汇总评测结果"""
        # 合并 retry 结果
        if (self.retry_failed or self._merge_mode) and self._existing_results:
            self.results = self._merge_retry_results(self.results)

        # 过滤出成功的结果
        success_results = [r for r in self.results if "error" not in r]
        
        if not success_results:
            raise RuntimeError("所有样本评测都失败了")

        # 计算各维度的统计量
        def calc_stats(scores: List[float]) -> Dict[str, float]:
            if len(scores) < 2:
                return {
                    "mean": round(scores[0] if scores else 0, 2),
                    "std": 0,
                    "min": round(scores[0] if scores else 0, 2),
                    "max": round(scores[0] if scores else 0, 2),
                }
            return {
                "mean": round(statistics.mean(scores), 2),
                "std": round(statistics.stdev(scores), 2),
                "min": round(min(scores), 2),
                "max": round(max(scores), 2),
            }

        photo_scores = [r["photo_score"] for r in success_results]
        story_scores = [r["story_score"] for r in success_results]
        interview_scores = [r["interview_score"] for r in success_results]
        final_scores = [r["final_score"] for r in success_results]

        aggregate = {
            "model_name": self.model_name,
            "eval_time": datetime.now().isoformat(),
            "provider": self.model_config.get("provider", ""),
            "configured_text_model": self.model_config.get("text_model", ""),
            "configured_vision_model": self.model_config.get("vision_model", ""),
            "total_samples": len(self.results),
            "successful_samples": len(success_results),
            "failed_samples": len(self.results) - len(success_results),
            "weights": self.weights,
            "photo": calc_stats(photo_scores),
            "story": calc_stats(story_scores),
            "interview": calc_stats(interview_scores),
            "final": calc_stats(final_scores),
            "samples": self.results,
        }

        # 保存结果到文件
        output_file = self.output_dir / f"{self.model_name}_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(aggregate, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] 结果已保存: {output_file}")
        return aggregate

    def print_summary(self, aggregate: Dict[str, Any]):
        """打印评测总结"""
        print(f"\n{'='*60}")
        print(f"模型: {self.model_name} - 评测完成")
        print(f"{'='*60}")
        print(f"样本总数: {aggregate['total_samples']}")
        print(f"成功: {aggregate['successful_samples']}")
        print(f"失败: {aggregate['failed_samples']}")
        print(f"\n{'指标':<12} {'平均分':<8} {'标准差':<8} {'最小分':<8} {'最大分':<8}")
        print("-" * 50)
        for metric_name in ["photo", "story", "interview", "final"]:
            stats = aggregate[metric_name]
            print(f"{metric_name:<12} {stats['mean']:<8.2f} {stats['std']:<8.2f} {stats['min']:<8.2f} {stats['max']:<8.2f}")


def main():
    parser = argparse.ArgumentParser(description="单模型完整评测")
    parser.add_argument("--model", help="要评测的模型名称")
    parser.add_argument("--all-models", action="store_true", help="评测 models.yaml 中所有启用的模型")
    parser.add_argument("--config", default="models.yaml", help="模型配置文件")
    parser.add_argument("--samples-file", default="simulation/config/test_samples.json", help="样本集 JSON 文件路径")
    parser.add_argument("--sample-id", default="", help="只评测指定 sample_id")
    parser.add_argument("--verbose", action="store_true", help="输出更多调试信息")
    parser.add_argument("--retry-failed", action="store_true", help="只重跑上次失败的样本")
    parser.add_argument("--output-tag", default="", help="输出目录后缀标签，如 'real' → evaluation/mimo_real")
    args = parser.parse_args()

    if not args.all_models and not args.model:
        parser.error("必须提供 --model，或使用 --all-models")

    config_path = CONFIG_DIR / args.config
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    model_names: List[str]
    if args.all_models:
        model_names = [
            name for name, item in config.get("models", {}).items()
            if item.get("enabled", False)
        ]
        if not model_names:
            raise SystemExit("models.yaml 中没有启用的模型")
    else:
        model_names = [args.model]

    exit_code = 0
    for model_name in model_names:
        try:
            evaluator = SingleModelEvaluator(
                model_name=model_name,
                config_file=args.config,
                sample_id=args.sample_id,
                samples_file=args.samples_file,
                verbose=args.verbose,
                retry_failed=args.retry_failed,
                output_tag=args.output_tag,
            )
            aggregate = evaluator.evaluate()
            evaluator.print_summary(aggregate)
        except Exception as e:
            exit_code = 1
            print(f"\n[FAIL] 模型 {model_name} 评测失败: {str(e)}", file=sys.stderr)

    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
