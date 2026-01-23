"""
评估Agent模块
构建具备特定人设和记忆库的"老人Agent"，用于自动化评估
"""
from typing import Dict, List, Optional
import random
import json
import os
import config


class EvaluationAgent:
    """评估Agent - 模拟真实用户（老人）"""
    
    def __init__(self, persona_file: str = None):
        """
        初始化评估Agent
        
        Args:
            persona_file: 人设文件路径（JSON格式）
        """
        self.persona = self._load_persona(persona_file)
        self.memory = []  # 记忆库
        self.max_memory_size = config.EVALUATION_AGENT_MEMORY_SIZE
    
    def _load_persona(self, persona_file: str = None) -> Dict:
        """
        加载人设
        
        Args:
            persona_file: 人设文件路径
            
        Returns:
            人设字典
        """
        if persona_file and os.path.exists(persona_file):
            with open(persona_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 默认人设
        return {
            "name": "张爷爷",
            "age": 75,
            "background": "退休教师，喜欢回忆过去",
            "personality": "温和、健谈、怀旧",
            "memory_style": "详细但有时会重复",
            "key_memories": [
                "小时候住在老城区",
                "年轻时当过教师",
                "喜欢拍照记录生活"
            ]
        }
    
    def answer_question(self, question: str, photo_context: Dict = None) -> str:
        """
        根据人设和记忆回答问题
        
        Args:
            question: 访谈问题
            photo_context: 照片上下文信息
            
        Returns:
            Agent的回答
        """
        # 检查记忆库中是否有相关信息
        relevant_memory = self._search_memory(question, photo_context)
        
        # 生成回答
        answer = self._generate_answer(question, photo_context, relevant_memory)
        
        # 更新记忆库
        self._update_memory(question, answer, photo_context)
        
        return answer
    
    def _search_memory(self, question: str, photo_context: Dict = None) -> List[Dict]:
        """在记忆库中搜索相关信息"""
        relevant = []
        
        for memory in self.memory:
            # 简单的关键词匹配（实际可以使用向量相似度）
            if any(keyword in question for keyword in memory.get('keywords', [])):
                relevant.append(memory)
        
        return relevant[:3]  # 返回最相关的3条记忆
    
    def _generate_answer(
        self,
        question: str,
        photo_context: Dict,
        relevant_memory: List[Dict]
    ) -> str:
        """
        生成回答
        
        Args:
            question: 问题
            photo_context: 照片上下文
            relevant_memory: 相关记忆
            
        Returns:
            生成的回答
        """
        # 基于人设和记忆生成回答
        # 这里提供模拟实现，实际可以使用LLM生成更真实的回答
        
        answer_templates = {
            "地点": "是的，那是{place}，我{time}住的地方。",
            "人物": "那是{person}，我们{relationship}。",
            "时间": "这张照片是{time}拍的，当时{event}。",
            "情感": "那时候{feeling}，现在想起来还是很{emotion}。"
        }
        
        # 根据问题类型选择回答模板
        if "哪里" in question or "地方" in question:
            return answer_templates["地点"].format(
                place=photo_context.get('background', '老城区'),
                time="小时候"
            )
        elif "谁" in question or "人" in question:
            return answer_templates["人物"].format(
                person="我的家人",
                relationship="是一家人"
            )
        elif "什么时候" in question or "时间" in question:
            return answer_templates["时间"].format(
                time="80年代",
                event="我们一家人聚在一起"
            )
        else:
            # 通用回答
            return f"嗯，{question}这个问题让我想起了很多往事。{self._get_random_memory_snippet()}"
    
    def _get_random_memory_snippet(self) -> str:
        """从人设的关键记忆中随机获取片段"""
        memories = self.persona.get("key_memories", [])
        if memories:
            return random.choice(memories) + "，那时候的生活虽然简单，但很充实。"
        return "那时候的生活虽然简单，但很充实。"
    
    def _update_memory(self, question: str, answer: str, photo_context: Dict = None):
        """更新记忆库"""
        memory_entry = {
            "question": question,
            "answer": answer,
            "photo_context": photo_context,
            "keywords": self._extract_keywords(question + " " + answer)
        }
        
        self.memory.append(memory_entry)
        
        # 限制记忆库大小
        if len(self.memory) > self.max_memory_size:
            self.memory = self.memory[-self.max_memory_size:]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简化版）"""
        # 实际应该使用更高级的NLP方法
        keywords = []
        common_words = ["照片", "人", "地方", "时间", "时候", "事情", "感觉"]
        for word in common_words:
            if word in text:
                keywords.append(word)
        return keywords
    
    def evaluate_interview(
        self,
        questions: List[str],
        photo_analysis: Dict
    ) -> Dict:
        """
        评估访谈质量
        
        Args:
            questions: 问题列表
            photo_analysis: 照片分析结果
            
        Returns:
            评估结果字典
        """
        qa_pairs = []
        
        # Agent回答所有问题
        for question in questions:
            answer = self.answer_question(question, photo_analysis)
            qa_pairs.append({
                "question": question,
                "answer": answer
            })
        
        # 计算评估指标
        evaluation = {
            "question_count": len(questions),
            "answer_quality": self._evaluate_answers(qa_pairs),
            "relevance": self._evaluate_relevance(questions, photo_analysis),
            "depth": self._evaluate_depth(qa_pairs),
            "qa_pairs": qa_pairs
        }
        
        return evaluation
    
    def _evaluate_answers(self, qa_pairs: List[Dict]) -> float:
        """评估回答质量（基于回答长度和详细程度）"""
        if not qa_pairs:
            return 0.0
        
        avg_length = sum(len(qa['answer']) for qa in qa_pairs) / len(qa_pairs)
        # 归一化到0-1
        return min(avg_length / 100, 1.0)
    
    def _evaluate_relevance(self, questions: List[str], photo_analysis: Dict) -> float:
        """评估问题与照片的相关性"""
        if not questions:
            return 0.0
        
        analysis_text = photo_analysis.get('overall_description', '')
        relevant_count = 0
        
        for question in questions:
            # 检查问题中的关键词是否在分析结果中出现
            if any(keyword in analysis_text for keyword in question[:10]):
                relevant_count += 1
        
        return relevant_count / len(questions)
    
    def _evaluate_depth(self, qa_pairs: List[Dict]) -> float:
        """评估问题挖掘的深度"""
        if not qa_pairs:
            return 0.0
        
        # 基于问题类型和回答详细程度
        depth_score = 0.0
        for qa in qa_pairs:
            question = qa['question']
            answer = qa['answer']
            
            # 深层问题关键词
            deep_keywords = ["为什么", "感觉", "意义", "影响", "回忆"]
            if any(kw in question for kw in deep_keywords):
                depth_score += 0.3
            
            # 回答详细程度
            if len(answer) > 50:
                depth_score += 0.2
        
        return min(depth_score / len(qa_pairs), 1.0)
    
    def reset(self):
        """重置Agent状态"""
        self.memory = []


# 修复导入
import os
