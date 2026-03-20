"""
命令行故事评分入口
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from src.story_judge import StoryJudge, format_judgement_for_cli


def _read_text_argument(text: str, file_path: str, field_name: str) -> str:
    if text and file_path:
        raise ValueError(f"{field_name} 不能同时使用文本参数和文件参数")
    if file_path:
        with open(file_path, "r", encoding="utf-8") as file_obj:
            return file_obj.read().strip()
    return (text or "").strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="对单篇故事进行 HANNA 六维评分")
    parser.add_argument("--story", help="直接传入故事文本")
    parser.add_argument("--story-file", help="从文件读取故事文本")
    parser.add_argument("--prompt", help="可选，故事对应的 prompt")
    parser.add_argument("--prompt-file", help="从文件读取 prompt")
    parser.add_argument("--reference", help="可选，参考故事或原始回忆录")
    parser.add_argument("--reference-file", help="从文件读取参考故事")
    parser.add_argument("--output", help="可选，将评分结果写入指定 JSON 文件")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    story = _read_text_argument(args.story, args.story_file, "story")
    if not story:
        parser.error("必须通过 --story 或 --story-file 提供故事文本")

    story_prompt = _read_text_argument(args.prompt, args.prompt_file, "prompt")
    reference_story = _read_text_argument(args.reference, args.reference_file, "reference")

    judge = StoryJudge()
    judgement = judge.judge_story(
        story=story,
        story_prompt=story_prompt or None,
        reference_story=reference_story or None,
    )
    output_text = format_judgement_for_cli(judgement)
    print(output_text)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file_obj:
            file_obj.write(output_text + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())