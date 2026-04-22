"""
运行单个 benchmark 样本的真实生成链路。
流程：图片分析 -> 问题生成 -> 基于 memoir_text 构造回答 -> 故事生成。
"""
import argparse
import json
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEMO_DIR = PROJECT_ROOT / "demo"

sys.path.insert(0, str(DEMO_DIR))
sys.path.insert(0, str(DEMO_DIR / "src"))

from src.dialogue_manager import DialogueManager
from src.multimodal_analyzer import MultimodalAnalyzer
from src.story_generator import StoryGenerator


def _load_text_file(file_path: str) -> str:
    path_text = str(file_path or "").strip()
    if not path_text:
        return ""

    path = Path(path_text)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[。！？!?；;\n])", text)
    sentences = [part.strip() for part in parts if part.strip()]
    if not sentences and text.strip():
        return [text.strip()]
    return sentences


def _extract_keywords(text: str) -> List[str]:
    keywords = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]{2,}", text)
    seen = set()
    result = []
    for keyword in keywords:
        normalized = keyword.strip().lower()
        if len(normalized) < 2 or normalized in seen:
            continue
        seen.add(normalized)
        result.append(keyword)
    return result


def _build_oracle_answer(question: str, memoir_text: str, image_description: str) -> str:
    source_text = (memoir_text or "").strip() or (image_description or "").strip()
    if not source_text:
        return "我一时想不起更多细节了，但这张照片对我很重要。"

    sentences = _split_sentences(source_text)
    keywords = _extract_keywords(question)
    scored_sentences = []

    for sentence in sentences:
        score = 0
        for keyword in keywords:
            if keyword in sentence:
                score += max(2, len(keyword))
        score += min(len(sentence), 120) / 120
        scored_sentences.append((score, sentence))

    scored_sentences.sort(key=lambda item: item[0], reverse=True)
    selected = []
    for _, sentence in scored_sentences[:2]:
        if sentence not in selected:
            selected.append(sentence)

    if not selected:
        selected = sentences[:2]

    answer = "".join(selected).strip()
    return answer or source_text[:120]


def _resolve_image_path(sample: Dict) -> str:
    image_path = str(sample.get("image_path", "")).strip()
    if not image_path:
        raise ValueError("样本缺少 image_path")

    path = Path(image_path)
    if path.is_absolute():
        return str(path)
    return str((PROJECT_ROOT / path).resolve())


def run_sample(sample: Dict) -> Dict:
    image_path = _resolve_image_path(sample)
    photo_id = sample.get("sample_id") or Path(image_path).name
    memoir_text = str(sample.get("memoir_text", "")).strip() or _load_text_file(sample.get("memoir_path", ""))
    interview_text = str(sample.get("interview_text", "")).strip() or _load_text_file(sample.get("interview_path", ""))
    image_description = str(sample.get("image_description", "")).strip()

    analyzer = MultimodalAnalyzer()
    dialogue_manager = DialogueManager()
    story_generator = StoryGenerator()

    with redirect_stdout(sys.stderr):
        analysis_result = analyzer.analyze_image(image_path=image_path)
        initial_questions = dialogue_manager.start_dialogue(
            photo_id=photo_id,
            analysis_result=analysis_result,
        )

    qa_history = []
    for question in initial_questions:
        answer = _build_oracle_answer(question, memoir_text or interview_text, image_description)
        qa_history.append({"question": question, "answer": answer})

    if not qa_history:
        fallback_question = "看到这张照片时，你最想讲给后辈听的是什么？"
        qa_history.append({
            "question": fallback_question,
            "answer": _build_oracle_answer(fallback_question, memoir_text or interview_text, image_description),
        })

    with redirect_stdout(sys.stderr):
        story = story_generator.generate_single_photo_story(
            photo_id=photo_id,
            analysis_result=analysis_result,
            qa_history=qa_history,
            narrative_style="personal",
        )

    return {
        "sample_id": sample.get("sample_id", photo_id),
        "image_path": image_path,
        "analysis_result": analysis_result,
        "qa_history": qa_history,
        "story": story,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="运行单个样本的生成链路")
    parser.add_argument("--sample-file", required=True, help="单个样本 JSON 文件")
    args = parser.parse_args()

    sample_path = Path(args.sample_file)
    with open(sample_path, "r", encoding="utf-8") as f:
        sample = json.load(f)

    result = run_sample(sample)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())