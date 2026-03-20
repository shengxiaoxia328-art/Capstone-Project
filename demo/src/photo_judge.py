"""
照片评分模块
基于图像理解 benchmark 任务对照片理解能力进行评分
"""
import base64
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

import config


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


class PhotoJudge:
    """对单张照片执行 benchmark 评分。"""

    def __init__(self, api_key: str = None, api_endpoint: str = None):
        if api_key and api_endpoint:
            self.api_key = api_key
            self.api_endpoint = api_endpoint
            self.backend = "custom"
        elif config.USE_HUNYUAN:
            self.api_key = config.HUNYUAN_API_KEY
            self.api_endpoint = config.HUNYUAN_API_ENDPOINT
            self.backend = "hunyuan"
        elif config.USE_GEMINI:
            self.api_key = config.GEMINI_API_KEY
            self.api_endpoint = config.GEMINI_API_ENDPOINT
            self.backend = "gemini"
        else:
            raise RuntimeError("未检测到可用的模型配置，请先在 demo/.env 中配置 Gemini 或混元 API。")

    def judge_photo(self, sample: Dict[str, Any], image_root: Optional[str] = None) -> Dict[str, Any]:
        image_path = self._resolve_image_path(sample.get("image_path", ""), image_root)
        if not image_path:
            raise ValueError("benchmark 样本缺少 image_path")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")

        image_base64, image_format = self._encode_image(image_path)
        image_description = self._describe_image(image_base64, image_format)

        mme_result = self._score_mme_tasks(
            image_base64=image_base64,
            image_format=image_format,
            tasks=sample.get("mme_tasks") or [],
        )
        mmbench_result = self._score_mmbench_tasks(
            image_base64=image_base64,
            image_format=image_format,
            tasks=sample.get("mmbench_tasks") or [],
        )
        hooks_result = self._score_hooks(
            description=image_description,
            hooks=sample.get("hooks") or [],
        )

        raw_total = round(
            mme_result["raw_score"] + mmbench_result["raw_score"] + hooks_result["raw_score"],
            2,
        )
        max_total = round(
            mme_result["max_score"] + mmbench_result["max_score"] + hooks_result["max_score"],
            2,
        )
        normalized_score = round((raw_total / max_total) * 5, 2) if max_total else 0.0

        return {
            "image_path": image_path,
            "image_description": image_description,
            "sample_reference_description": str(sample.get("image_description", "")).strip(),
            "mme": mme_result,
            "mmbench": mmbench_result,
            "hooks": hooks_result,
            "raw_score": raw_total,
            "max_score": max_total,
            "normalized_score": normalized_score,
            "accuracy": round((raw_total / max_total) * 100, 2) if max_total else 0.0,
            "meta": {
                "backend": self.backend,
                "model": self._get_model_name(),
                "scale": "0-5",
            },
        }

    def _get_model_name(self) -> str:
        if self.backend == "hunyuan":
            return getattr(config, "HUNYUAN_VISION_MODEL", "hunyuan-vision")
        if self.backend == "gemini":
            return getattr(config, "GEMINI_MODEL_NAME", "gemini-2.5-pro")
        return "custom"

    def _resolve_image_path(self, image_path: str, image_root: Optional[str]) -> str:
        image_path = str(image_path or "").strip()
        if not image_path:
            return ""
        if os.path.isabs(image_path):
            return image_path
        if image_root:
            return os.path.normpath(os.path.join(image_root, image_path))
        return os.path.normpath(image_path)

    def _encode_image(self, image_path: str) -> Tuple[str, str]:
        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
        extension = os.path.splitext(image_path)[1].lower()
        image_format = "jpeg"
        if extension == ".png":
            image_format = "png"
        elif extension == ".gif":
            image_format = "gif"
        elif extension == ".webp":
            image_format = "webp"
        return image_base64, image_format

    def _describe_image(self, image_base64: str, image_format: str) -> str:
        prompt = (
            "请用简洁但具体的中文描述这张老照片，重点覆盖人物、场景、动作、服饰、时代线索、"
            "可见物品和整体氛围。不要编造看不见的细节，输出一段自然语言。"
        )
        return self._call_vision_api(image_base64, prompt, image_format)

    def _score_mme_tasks(self, image_base64: str, image_format: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        details = []
        raw_score = 0.0
        max_score = float(len(tasks))

        for task in tasks:
            question = str(task.get("question", "")).strip()
            expected = self._normalize_yes_no(task.get("answer"))
            if not question or expected is None:
                continue

            response = self._call_vision_api(
                image_base64,
                f"请只回答 yes 或 no，不要添加任何解释。问题：{question}",
                image_format,
            )
            predicted = self._normalize_yes_no(response)
            correct = predicted == expected
            if correct:
                raw_score += 1.0

            details.append(
                {
                    "question": question,
                    "expected": expected,
                    "predicted": predicted or "unknown",
                    "raw_response": response,
                    "correct": correct,
                    "score": 1.0 if correct else 0.0,
                }
            )

        max_score = float(len(details))
        return {
            "details": details,
            "raw_score": round(raw_score, 2),
            "max_score": round(max_score, 2),
            "normalized_score": round((raw_score / max_score) * 5, 2) if max_score else 0.0,
        }

    def _score_mmbench_tasks(self, image_base64: str, image_format: str, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        details = []
        raw_score = 0.0

        for task in tasks:
            question = str(task.get("question", "")).strip()
            options = task.get("options") or {}
            answer = str(task.get("answer", "")).strip().upper()
            if not question or not options or answer not in options:
                continue

            option_lines = []
            for key in sorted(options):
                option_lines.append(f"{key}. {options[key]}")
            option_text = "\n".join(option_lines)
            prompt = (
                "请阅读图片并回答下面的选择题。"
                "只输出一个选项字母，不要输出解释。\n"
                f"问题：{question}\n"
                f"选项：\n{option_text}"
            )
            response = self._call_vision_api(image_base64, prompt, image_format)
            predicted = self._extract_choice(response)
            correct = predicted == answer
            if correct:
                raw_score += 1.0

            details.append(
                {
                    "question": question,
                    "options": options,
                    "expected": answer,
                    "predicted": predicted or "unknown",
                    "raw_response": response,
                    "correct": correct,
                    "score": 1.0 if correct else 0.0,
                }
            )

        max_score = float(len(details))
        return {
            "details": details,
            "raw_score": round(raw_score, 2),
            "max_score": round(max_score, 2),
            "normalized_score": round((raw_score / max_score) * 5, 2) if max_score else 0.0,
        }

    def _score_hooks(self, description: str, hooks: List[str]) -> Dict[str, Any]:
        details = []
        raw_score = 0.0

        for hook in hooks:
            hook_text = str(hook or "").strip()
            if not hook_text:
                continue

            exact_match = self._contains_hook(description, hook_text)
            semantic_match = False
            if exact_match:
                score = 1.0
            else:
                semantic_match = self._judge_hook_semantic_match(description, hook_text)
                score = 1.0 if semantic_match else 0.0

            raw_score += score
            details.append(
                {
                    "hook": hook_text,
                    "exact_match": exact_match,
                    "semantic_match": semantic_match,
                    "score": score,
                }
            )

        max_score = float(len(details))
        return {
            "details": details,
            "raw_score": round(raw_score, 2),
            "max_score": round(max_score, 2),
            "normalized_score": round((raw_score / max_score) * 5, 2) if max_score else 0.0,
        }

    def _contains_hook(self, description: str, hook: str) -> bool:
        clean_description = self._normalize_text(description)
        clean_hook = self._normalize_text(hook)
        return bool(clean_hook) and clean_hook in clean_description

    def _judge_hook_semantic_match(self, description: str, hook: str) -> bool:
        prompt = f"""你是照片理解评估员。请判断“照片描述”是否已经明确提到了“关键叙事钩子”的核心含义。

要求：
1. 只回答 yes 或 no。
2. 只有在描述中已经明确表达出该钩子的核心信息时才回答 yes。
3. 如果只是模糊相关、可能暗示、或需要过度推断，一律回答 no。

照片描述：
{description}

关键叙事钩子：
{hook}
"""
        response = self._call_text_api(prompt)
        return self._normalize_yes_no(response) == "yes"

    def _normalize_yes_no(self, value: Any) -> Optional[str]:
        text = self._normalize_text(value)
        if not text:
            return None
        if any(token in text for token in ["yes", "是", "有", "存在", "正确"]):
            return "yes"
        if any(token in text for token in ["no", "否", "没有", "不存在", "错误"]):
            return "no"
        return None

    def _extract_choice(self, value: Any) -> Optional[str]:
        text = str(value or "").upper()
        match = re.search(r"\b([A-D])\b", text)
        if match:
            return match.group(1)
        compact = re.sub(r"[^A-D]", "", text)
        if compact:
            return compact[0]
        return None

    def _normalize_text(self, value: Any) -> str:
        text = str(value or "").strip().lower()
        text = re.sub(r"\s+", "", text)
        text = re.sub(r"[，。！？；：、“”‘’\"'（）()\[\]{}<>《》,.!?;:/\\-]", "", text)
        return text

    def _call_text_api(self, prompt: str) -> str:
        if self.backend == "hunyuan":
            return self._call_hunyuan_text_api(prompt)
        return self._call_gemini_text_api(prompt)

    def _call_vision_api(self, image_base64: str, prompt: str, image_format: str) -> str:
        if self.backend == "hunyuan":
            return self._call_hunyuan_vision_api(image_base64, prompt, image_format)
        return self._call_gemini_vision_api(image_base64, prompt, image_format)

    def _call_hunyuan_text_api(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": getattr(config, "HUNYUAN_TEXT_MODEL", "hunyuan-vision"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        response = requests.post(
            self.api_endpoint,
            headers=headers,
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        result = response.json()
        choices = result.get("choices") or []
        if not choices:
            raise RuntimeError(f"混元文本接口返回格式异常: {result}")
        return choices[0]["message"]["content"]

    def _call_hunyuan_vision_api(self, image_base64: str, prompt: str, image_format: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": getattr(config, "HUNYUAN_VISION_MODEL", "hunyuan-vision"),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format if image_format in ('png', 'gif', 'webp') else 'jpeg'};base64,{image_base64}"
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
            "temperature": 0.2,
        }
        response = requests.post(
            self.api_endpoint,
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        choices = result.get("choices") or []
        if not choices:
            raise RuntimeError(f"混元视觉接口返回格式异常: {result}")
        return choices[0]["message"]["content"]

    def _call_gemini_text_api(self, prompt: str) -> str:
        model_name = getattr(config, "GEMINI_MODEL_NAME", "gemini-2.5-pro")
        base = (self.api_endpoint or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
            },
        }

        if "generativelanguage.googleapis.com" in base:
            url = f"{base}/models/{model_name}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            }
        else:
            url = f"{base}/models/{model_name}:generateContent"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

        response = requests.post(url, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        return self._extract_gemini_text(response.json())

    def _call_gemini_vision_api(self, image_base64: str, prompt: str, image_format: str) -> str:
        model_name = getattr(config, "GEMINI_MODEL_NAME", "gemini-2.5-pro")
        base = (self.api_endpoint or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": self._get_mime_type(image_format),
                                "data": image_base64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
            },
        }

        if "generativelanguage.googleapis.com" in base:
            url = f"{base}/models/{model_name}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            }
        else:
            url = f"{base}/models/{model_name}:generateContent"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return self._extract_gemini_text(response.json())

    def _extract_gemini_text(self, result: Dict[str, Any]) -> str:
        candidates = result.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"Gemini 返回格式异常: {result}")
        parts = candidates[0].get("content", {}).get("parts", [])
        texts = [part.get("text", "") for part in parts if part.get("text")]
        if not texts:
            raise RuntimeError(f"Gemini 未返回文本内容: {result}")
        return "\n".join(texts)

    def _get_mime_type(self, image_format: str) -> str:
        mapping = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
        }
        return mapping.get((image_format or "jpeg").lower(), "image/jpeg")


def load_benchmark_sample(benchmark_file: str, sample_index: int = 0) -> Dict[str, Any]:
    with open(benchmark_file, "r", encoding="utf-8") as file_obj:
        data = json.load(file_obj)

    if isinstance(data, dict):
        if "samples" in data and isinstance(data["samples"], list):
            samples = data["samples"]
        else:
            return data
    elif isinstance(data, list):
        samples = data
    else:
        raise ValueError("benchmark 文件必须是对象或数组")

    if not samples:
        raise ValueError("benchmark 文件中没有可用样本")
    if sample_index < 0 or sample_index >= len(samples):
        raise IndexError(f"sample_index 超出范围: {sample_index}，共有 {len(samples)} 条样本")
    return samples[sample_index]


def format_photo_judgement_for_cli(judgement: Dict[str, Any]) -> str:
    output = {
        "image_path": judgement["image_path"],
        "raw_score": judgement["raw_score"],
        "max_score": judgement["max_score"],
        "normalized_score": judgement["normalized_score"],
        "accuracy": judgement["accuracy"],
        "image_description": judgement["image_description"],
        "mme": judgement["mme"],
        "mmbench": judgement["mmbench"],
        "hooks": judgement["hooks"],
        "meta": judgement.get("meta", {}),
    }
    return json.dumps(output, ensure_ascii=False, indent=2)