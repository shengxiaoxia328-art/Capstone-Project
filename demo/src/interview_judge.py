"""
访谈评分模块
基于追问质量、回答质量和信息覆盖度对问答过程进行评分
"""
from typing import Any, Dict, List

from .enhanced_followup import AnswerQualityAnalyzer, InformationGapIdentifier


DEEP_QUESTION_KEYWORDS = [
    "为什么", "感觉", "意义", "影响", "后来", "当时", "记得", "想起", "怎么",
]


class InterviewJudge:
    """对访谈问答历史进行 0-5 分评分。"""

    def __init__(self):
        self.quality_analyzer = AnswerQualityAnalyzer()
        self.gap_identifier = InformationGapIdentifier()

    def judge_interview(self, qa_history: List[Dict[str, Any]], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        if not qa_history:
            raise ValueError("qa_history 不能为空")

        normalized_history = self._normalize_history(qa_history)
        if not normalized_history:
            raise ValueError("qa_history 中没有有效的 question/answer 对")

        answer_qualities = [
            self.quality_analyzer.analyze(item["answer"])
            for item in normalized_history
        ]
        average_answer_quality = sum(item["quality_score"] for item in answer_qualities) / len(answer_qualities)

        discussed_dimensions = self._collect_discussed_dimensions(normalized_history)
        total_dimensions = len(InformationGapIdentifier.KEY_DIMENSIONS)
        coverage_score = len(discussed_dimensions) / total_dimensions if total_dimensions else 0.0

        remaining_gaps = self.gap_identifier.identify_gaps(normalized_history, analysis_result)
        completeness_score = 1.0 - (len(remaining_gaps) / total_dimensions if total_dimensions else 0.0)
        completeness_score = max(0.0, completeness_score)

        deep_question_hits = sum(
            1
            for item in normalized_history
            if any(keyword in item["question"] for keyword in DEEP_QUESTION_KEYWORDS)
        )
        depth_score = deep_question_hits / len(normalized_history)

        final_score_0_1 = (
            average_answer_quality * 0.35
            + completeness_score * 0.35
            + depth_score * 0.2
            + coverage_score * 0.1
        )
        final_score = round(final_score_0_1 * 5, 2)

        return {
            "metrics": {
                "answer_quality": round(average_answer_quality * 5, 2),
                "information_completeness": round(completeness_score * 5, 2),
                "question_depth": round(depth_score * 5, 2),
                "topic_coverage": round(coverage_score * 5, 2),
            },
            "discussed_dimensions": sorted(discussed_dimensions),
            "remaining_gaps": sorted(remaining_gaps),
            "question_count": len(normalized_history),
            "final_score": final_score,
            "meta": {
                "scale": "0-5",
                "standard": "pr2-followup-quality",
            },
        }

    def _normalize_history(self, qa_history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        normalized = []
        for item in qa_history:
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if question and answer:
                normalized.append({"question": question, "answer": answer})
        return normalized

    def _collect_discussed_dimensions(self, qa_history: List[Dict[str, str]]) -> List[str]:
        discussed = set()
        for item in qa_history:
            combined = (item["question"] + " " + item["answer"]).lower()
            for dimension, keywords in InformationGapIdentifier.KEY_DIMENSIONS.items():
                if any(keyword in combined for keyword in keywords):
                    discussed.add(dimension)
        return list(discussed)