"""
增强的追问机制模块
基于学术论文研究改进追问策略
"""
from typing import Dict, List, Optional, Tuple
import re


class AnswerQualityAnalyzer:
    """回答质量分析器"""
    
    @staticmethod
    def analyze(answer: str) -> Dict:
        """
        分析回答质量
        
        Returns:
            包含质量指标的字典
        """
        length = len(answer.strip())
        
        # 详细程度评估
        detail_level = "low"
        if length > 100:
            detail_level = "high"
        elif length > 50:
            detail_level = "medium"
        
        # 情感检测
        emotion_keywords = ["感觉", "心情", "开心", "难过", "激动", "怀念", "温暖", 
                           "感动", "难忘", "珍贵", "意义", "影响"]
        emotion_present = any(keyword in answer for keyword in emotion_keywords)
        
        # 信息密度（基于关键词数量）
        info_keywords = ["因为", "所以", "当时", "后来", "记得", "想起", 
                        "地点", "时间", "人物", "关系"]
        keyword_count = sum(1 for kw in info_keywords if kw in answer)
        information_density = min(keyword_count / 5.0, 1.0)
        
        # 具体性（包含具体细节）
        specific_indicators = ["在", "和", "的", "了", "是", "有"]
        specificity = min(sum(1 for ind in specific_indicators if ind in answer) / 10.0, 1.0)
        
        return {
            "length": length,
            "detail_level": detail_level,
            "emotion_present": emotion_present,
            "information_density": information_density,
            "specificity": specificity,
            "quality_score": (information_density * 0.4 + specificity * 0.3 + 
                             (1.0 if emotion_present else 0.0) * 0.3)
        }


class InformationGapIdentifier:
    """信息缺口识别器"""
    
    # 关键信息维度
    KEY_DIMENSIONS = {
        "人物": ["谁", "人物", "人", "关系", "家人", "朋友"],
        "地点": ["哪里", "地方", "地点", "位置", "背景"],
        "时间": ["什么时候", "时间", "年代", "时期", "年份"],
        "情感": ["感觉", "心情", "情感", "意义", "影响"],
        "事件": ["发生", "事情", "经过", "过程", "故事"],
        "细节": ["细节", "具体", "详细", "特征", "特点"]
    }
    
    @staticmethod
    def identify_gaps(qa_history: List[Dict], 
                      analysis_result: Dict) -> List[str]:
        """
        识别信息缺口
        
        Args:
            qa_history: 问答历史
            analysis_result: 照片分析结果
            
        Returns:
            信息缺口列表
        """
        gaps = []
        
        # 收集已讨论的话题
        discussed_topics = set()
        for qa in qa_history:
            question = qa.get("question", "").lower()
            answer = qa.get("answer", "").lower()
            combined = question + " " + answer
            
            for dimension, keywords in InformationGapIdentifier.KEY_DIMENSIONS.items():
                if any(kw in combined for kw in keywords):
                    discussed_topics.add(dimension)
        
        # 检查分析结果中提到的关键信息是否已讨论
        analysis_text = str(analysis_result.get("overall_description", "")).lower()
        
        for dimension, keywords in InformationGapIdentifier.KEY_DIMENSIONS.items():
            # 如果分析结果提到但未讨论
            if any(kw in analysis_text for kw in keywords) and dimension not in discussed_topics:
                gaps.append(dimension)
        
        # 检查关键维度是否缺失
        critical_dimensions = ["人物", "地点", "时间"]
        for dim in critical_dimensions:
            if dim not in discussed_topics and dim not in gaps:
                gaps.append(dim)
        
        # 去重并返回
        return list(set(gaps))


class QuestionTypeSelector:
    """问题类型选择器"""
    
    QUESTION_TYPES = {
        "clarification": {
            "description": "澄清性问题 - 当回答不够详细时",
            "keywords": ["能详细", "具体", "可以多说", "请详细"]
        },
        "emotion_deepening": {
            "description": "情感深化 - 当回答包含情感时",
            "keywords": ["为什么", "感觉", "意义", "影响", "对你来说"]
        },
        "detail_expansion": {
            "description": "细节扩展 - 当需要更多细节时",
            "keywords": ["还有", "其他", "另外", "细节", "具体"]
        },
        "connection": {
            "description": "关联性问题 - 连接不同信息",
            "keywords": ["关系", "关联", "联系", "和", "与"]
        },
        "contextual": {
            "description": "上下文问题 - 基于照片分析",
            "keywords": ["照片中", "看", "注意到", "背景"]
        }
    }
    
    @staticmethod
    def select_type(answer_quality: Dict, 
                   information_gaps: List[str],
                   qa_history: List[Dict]) -> str:
        """
        选择问题类型
        
        Args:
            answer_quality: 回答质量分析结果
            information_gaps: 信息缺口列表
            qa_history: 问答历史
            
        Returns:
            问题类型
        """
        # 如果回答质量低，使用澄清性问题
        if answer_quality["quality_score"] < 0.3:
            return "clarification"
        
        # 如果有情感但未深入，使用情感深化
        if answer_quality["emotion_present"] and answer_quality["quality_score"] < 0.7:
            return "emotion_deepening"
        
        # 如果有信息缺口，使用上下文问题
        if information_gaps:
            return "contextual"
        
        # 如果信息密度低，使用细节扩展
        if answer_quality["information_density"] < 0.5:
            return "detail_expansion"
        
        # 默认使用关联性问题
        return "connection"


class EnhancedFollowupGenerator:
    """增强的追问生成器"""
    
    def __init__(self):
        self.quality_analyzer = AnswerQualityAnalyzer()
        self.gap_identifier = InformationGapIdentifier()
        self.type_selector = QuestionTypeSelector()
    
    def generate_enhanced_followup_prompt(
        self,
        analysis_result: Dict,
        previous_qa: List[Dict],
        context: Optional[Dict] = None
    ) -> str:
        """
        生成增强的追问提示词
        
        Args:
            analysis_result: 照片分析结果
            previous_qa: 之前的问答对
            context: 上下文信息
            
        Returns:
            增强的提示词
        """
        # 分析最后一个回答的质量
        if previous_qa:
            last_answer = previous_qa[-1].get("answer", "")
            answer_quality = self.quality_analyzer.analyze(last_answer)
        else:
            answer_quality = {"quality_score": 0.5, "emotion_present": False, 
                            "information_density": 0.5}
        
        # 识别信息缺口
        information_gaps = self.gap_identifier.identify_gaps(previous_qa, analysis_result)
        
        # 选择问题类型
        question_type = self.type_selector.select_type(
            answer_quality, information_gaps, previous_qa
        )
        
        # 构建对话历史摘要
        qa_summary = self._summarize_qa(previous_qa)
        
        # 构建增强提示词
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

信息缺口（需要深入挖掘的方面）：
{', '.join(information_gaps) if information_gaps else '无明显缺口，可进行情感深化或关联性提问'}

问题类型：{question_type}
- {QuestionTypeSelector.QUESTION_TYPES[question_type]['description']}

要求：
1. 根据回答质量分析，如果回答不够详细，生成澄清性问题
2. 如果回答包含情感，生成情感深化问题，挖掘更深层的情感体验
3. 针对信息缺口，生成能够填补缺口的问题
4. 避免重复之前的问题
5. 问题要自然、对话式，能够引导用户深入回忆
6. 结合照片中的视觉特征和对话历史

问题生成策略：
"""
        
        # 根据问题类型添加特定指导
        if question_type == "clarification":
            prompt += "- 使用澄清性问题，如'能详细说说...吗？'或'可以具体描述一下...吗？'\n"
        elif question_type == "emotion_deepening":
            prompt += "- 使用情感深化问题，如'当时你是什么感觉？'或'这对你来说有什么特殊意义？'\n"
        elif question_type == "detail_expansion":
            prompt += "- 使用细节扩展问题，如'还有哪些细节让你印象深刻？'或'能说说其他相关的事情吗？'\n"
        elif question_type == "connection":
            prompt += "- 使用关联性问题，连接不同信息点，如'这和之前提到的...有什么关系？'\n"
        else:
            prompt += "- 结合照片中的视觉特征提问，如'看照片中的...，这让你想起了什么？'\n"
        
        prompt += """
重要：直接输出一个问题，不要任何思考过程、解释或元信息。
直接开始输出问题，格式如下（不要任何前缀）：
[直接输出中文问题]

只输出中文问题，不要其他内容。"""
        
        return prompt
    
    def _summarize_qa(self, qa_list: List[Dict], max_length: int = 300) -> str:
        """总结问答对，保留关键信息"""
        if not qa_list:
            return "暂无对话历史"
        
        summary_parts = []
        for i, qa in enumerate(qa_list[-3:], 1):  # 只保留最近3轮
            q = qa.get('question', '')[:50]
            a = qa.get('answer', '')[:100]
            summary_parts.append(f"Q{i}: {q}\nA{i}: {a}")
        
        summary = "\n".join(summary_parts)
        
        # 如果太长，进一步压缩
        if len(summary) > max_length:
            # 只保留问题和答案的关键部分
            compressed = []
            for qa in qa_list[-2:]:  # 只保留最近2轮
                q = qa.get('question', '')[:40]
                a = qa.get('answer', '')[:60]
                compressed.append(f"Q: {q} A: {a}")
            summary = "\n".join(compressed)
        
        return summary
