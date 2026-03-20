"""
照片分与故事分的融合评分入口
"""
import argparse
import json
import os
import sys
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from src.photo_judge import PhotoJudge, load_benchmark_sample
from src.story_judge import StoryJudge


def _read_text_argument(text: str, file_path: str, field_name: str) -> str:
    if text and file_path:
        raise ValueError(f"{field_name} 不能同时使用文本参数和文件参数")
    if file_path:
        with open(file_path, "r", encoding="utf-8") as file_obj:
            return file_obj.read().strip()
    return (text or "").strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="融合照片 benchmark 与 HANNA 故事评分")
    parser.add_argument("--benchmark-file", required=True, help="照片 benchmark JSON 文件")
    parser.add_argument("--sample-index", type=int, default=0, help="当 benchmark 文件包含多个样本时，选择第几条")
    parser.add_argument("--image-root", help="可选，图片相对路径的根目录")
    parser.add_argument("--story", help="直接传入故事文本")
    parser.add_argument("--story-file", help="从文件读取故事文本")
    parser.add_argument("--prompt", help="可选，故事对应的 prompt")
    parser.add_argument("--prompt-file", help="从文件读取 prompt")
    parser.add_argument("--reference", help="可选，参考故事或原始回忆录")
    parser.add_argument("--reference-file", help="从文件读取参考故事")
    parser.add_argument("--photo-weight", type=float, default=0.5, help="照片分权重，默认 0.5")
    parser.add_argument("--story-weight", type=float, default=0.5, help="故事分权重，默认 0.5")
    parser.add_argument("--output", help="可选，将结果写入指定 JSON 文件")
    return parser


def _validate_weights(photo_weight: float, story_weight: float) -> Dict[str, float]:
    if photo_weight < 0 or story_weight < 0:
        raise ValueError("权重不能为负数")
    total = photo_weight + story_weight
    if total <= 0:
        raise ValueError("photo_weight 与 story_weight 之和必须大于 0")
    return {
        "photo": round(photo_weight / total, 4),
        "story": round(story_weight / total, 4),
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    story = _read_text_argument(args.story, args.story_file, "story")
    if not story:
        parser.error("必须通过 --story 或 --story-file 提供故事文本")

    story_prompt = _read_text_argument(args.prompt, args.prompt_file, "prompt")
    reference_story = _read_text_argument(args.reference, args.reference_file, "reference")
    weights = _validate_weights(args.photo_weight, args.story_weight)

    sample = load_benchmark_sample(args.benchmark_file, args.sample_index)

    photo_judge = PhotoJudge()
    story_judge = StoryJudge()

    photo_result = photo_judge.judge_photo(sample=sample, image_root=args.image_root)
    story_result = story_judge.judge_story(
        story=story,
        story_prompt=story_prompt or None,
        reference_story=reference_story or None,
    )

    final_score = round(
        photo_result["normalized_score"] * weights["photo"]
        + story_result["final_score"] * weights["story"],
        2,
    )

    output = {
        "final_score": final_score,
        "weights": weights,
        "photo_evaluation": {
            "raw_score": photo_result["raw_score"],
            "max_score": photo_result["max_score"],
            "normalized_score": photo_result["normalized_score"],
            "accuracy": photo_result["accuracy"],
            "image_path": photo_result["image_path"],
            "image_description": photo_result["image_description"],
            "mme": photo_result["mme"],
            "mmbench": photo_result["mmbench"],
            "hooks": photo_result["hooks"],
            "meta": photo_result.get("meta", {}),
        },
        "story_evaluation": story_result,
        "meta": {
            "sample_index": args.sample_index,
            "benchmark_file": args.benchmark_file,
            "score_scale": "0-5",
        },
    }

    output_text = json.dumps(output, ensure_ascii=False, indent=2)
    print(output_text)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file_obj:
            file_obj.write(output_text + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())