"""
增强的追问机制模块
基于回答质量和信息缺口动态调整追问策略
"""
from typing import Dict, List, Optional


class AnswerQualityAnalyzer:
    """回答质量分析器"""

    @staticmethod
    def analyze(answer: str) -> Dict:
        """分析回答的详细度、情感和信息密度。"""
        length = len(answer.strip())

        detail_level = "low"
        if length > 100:
            detail_level = "high"
        elif length > 50:
            detail_level = "medium"

        emotion_keywords = [
            "感觉", "心情", "开心", "难过", "激动", "怀念", "温暖",
            "感动", "难忘", "珍贵", "意义", "影响",
        ]
        emotion_present = any(keyword in answer for keyword in emotion_keywords)

        info_keywords = [
            "因为", "所以", "当时", "后来", "记得", "想起",
            "地点", "时间", "人物", "关系",
        ]
        keyword_count = sum(1 for keyword in info_keywords if keyword in answer)
        information_density = min(keyword_count / 5.0, 1.0)

        specific_indicators = ["在", "和", "的", "了", "是", "有"]
        specificity = min(sum(1 for item in specific_indicators if item in answer) / 10.0, 1.0)

        return {
            "length": length,
            "detail_level": detail_level,
            "emotion_present": emotion_present,
            "information_density": information_density,
            "specificity": specificity,
            "quality_score": (
                information_density * 0.4
                + specificity * 0.3
                + (1.0 if emotion_present else 0.0) * 0.3
            ),
        }


class InformationGapIdentifier:
    """信息缺口识别器"""

    KEY_DIMENSIONS = {
        "人物": ["谁", "人物", "人", "关系", "家人", "朋友"],
        "地点": ["哪里", "地方", "地点", "位置", "背景"],
        "时间": ["什么时候", "时间", "年代", "时期", "年份"],
        "情感": ["感觉", "心情", "情感", "意义", "影响"],
        "事件": ["发生", "事情", "经过", "过程", "故事"],
        "细节": ["细节", "具体", "详细", "特征", "特点"],
    }

    @staticmethod
    def identify_gaps(qa_history: List[Dict], analysis_result: Dict) -> List[str]:
        """识别当前问答中仍未覆盖的关键信息维度。"""
        gaps = []
        discussed_topics = set()

        for qa in qa_history:
            question = qa.get("question", "").lower()
            answer = qa.get("answer", "").lower()
            combined = question + " " + answer

            for dimension, keywords in InformationGapIdentifier.KEY_DIMENSIONS.items():
                if any(keyword in combined for keyword in keywords):
                    discussed_topics.add(dimension)

        analysis_text = str(analysis_result.get("overall_description", "")).lower()
        for dimension, keywords in InformationGapIdentifier.KEY_DIMENSIONS.items():
            if any(keyword in analysis_text for keyword in keywords) and dimension not in discussed_topics:
                gaps.append(dimension)

        for dimension in ["人物", "地点", "时间"]:
            if dimension not in discussed_topics and dimension not in gaps:
                gaps.append(dimension)

        return list(set(gaps))


class QuestionTypeSelector:
    """根据回答质量选择追问类型"""

    QUESTION_TYPES = {
        "clarification": "澄清性问题",
        "emotion_deepening": "情感深化问题",
        "detail_expansion": "细节扩展问题",
        "connection": "关联性问题",
        "contextual": "结合照片细节的问题",
    }

    @staticmethod
    def select_type(answer_quality: Dict, information_gaps: List[str], qa_history: List[Dict]) -> str:
        """选择最合适的追问类型。"""
        if answer_quality["quality_score"] < 0.3:
            return "clarification"

        if answer_quality["emotion_present"] and answer_quality["quality_score"] < 0.7:
            return "emotion_deepening"

        if information_gaps:
            return "contextual"

        if answer_quality["information_density"] < 0.5:
            return "detail_expansion"

        return "connection"


class EnhancedFollowupGenerator:
    """增强追问生成器"""

    def __init__(self):
        self.quality_analyzer = AnswerQualityAnalyzer()
        self.gap_identifier = InformationGapIdentifier()
        self.type_selector = QuestionTypeSelector()

    def generate_enhanced_followup_prompt(
        self,
        analysis_result: Dict,
        previous_qa: List[Dict],
        context: Optional[Dict] = None,
    ) -> str:
        """生成用于大模型的增强追问提示词。"""
        if previous_qa:
            last_answer = previous_qa[-1].get("answer", "")
            answer_quality = self.quality_analyzer.analyze(last_answer)
        else:
            answer_quality = {
                "quality_score": 0.5,
                "detail_level": "medium",
                "emotion_present": False,
                "information_density": 0.5,
            }

        information_gaps = self.gap_identifier.identify_gaps(previous_qa, analysis_result)
        question_type = self.type_selector.select_type(answer_quality, information_gaps, previous_qa)
        qa_summary = self._summarize_qa(previous_qa)

        prompt = f"""基于以下信息，生成一个深入的后续访谈问题：

照片信息：
{analysis_result.get('overall_description', '')[:300]}

之前的对话历史：
{qa_summary}

回答质量分析：
- 详细程度：{answer_quality.get('detail_level', 'medium')}
- 包含情感：{'是' if answer_quality.get('emotion_present') else '否'}
- 信息密度：{answer_quality.get('information_density', 0.5):.2f}
- 质量评分：{answer_quality.get('quality_score', 0.5):.2f}

信息缺口：
{', '.join(information_gaps) if information_gaps else '无明显缺口，可继续深入情感或事件细节'}

问题类型：{question_type}（{QuestionTypeSelector.QUESTION_TYPES[question_type]}）

要求：
1. 根据回答质量生成追问，回答太短时优先澄清与细化。
2. 若回答提到感受或意义，优先追问情感体验。
3. 若仍存在信息缺口，优先围绕缺失的维度发问。
4. 避免重复之前的问题。
5. 问题要自然、口语化、适合访谈场景。
6. 结合照片中的视觉特征和已有对话。
"""

        if question_type == "clarification":
            prompt += "\n策略：用‘能详细说说……吗’‘可以具体讲讲……吗’这类澄清方式。\n"
        elif question_type == "emotion_deepening":
            prompt += "\n策略：优先追问‘当时你是什么感觉’‘这对你意味着什么’。\n"
        elif question_type == "detail_expansion":
            prompt += "\n策略：优先追问更多细节、补充人物事件和场景信息。\n"
        elif question_type == "connection":
            prompt += "\n策略：把前面提到的人、地点、事件串联起来追问。\n"
        else:
            prompt += "\n策略：从照片中的人物、背景、物品或时代线索切入提问。\n"

        if context:
            prompt += f"\n上下文：\n{context}\n"

        prompt += """

重要：直接输出一个中文问题，不要思考过程，不要解释，不要编号。
只输出问题本身。
"""
        return prompt

    def _summarize_qa(self, qa_list: List[Dict], max_length: int = 300) -> str:
        """压缩最近几轮问答，用于构造追问上下文。"""
        if not qa_list:
            return "暂无对话历史"

        summary_parts = []
        for index, qa in enumerate(qa_list[-3:], 1):
            question = qa.get("question", "")[:50]
            answer = qa.get("answer", "")[:100]
            summary_parts.append(f"Q{index}: {question}\nA{index}: {answer}")

        summary = "\n".join(summary_parts)
        if len(summary) <= max_length:
            return summary

        compressed_parts = []
        for qa in qa_list[-2:]:
            question = qa.get("question", "")[:40]
            answer = qa.get("answer", "")[:60]
            compressed_parts.append(f"Q: {question} A: {answer}")
        return "\n".join(compressed_parts)