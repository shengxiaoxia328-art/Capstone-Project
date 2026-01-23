"""
对话管理模块
管理单张照片的多轮对话
"""
from typing import Dict, List, Optional
import config


class DialogueManager:
    """对话管理器"""
    
    def __init__(self):
        """初始化对话管理器"""
        self.current_photo_id: Optional[str] = None
        self.analysis_result: Optional[Dict] = None
        self.qa_history: List[Dict] = []
        self.max_rounds = config.MAX_DIALOGUE_ROUNDS
    
    def start_dialogue(self, photo_id: str, analysis_result: Dict) -> List[str]:
        """
        开始新的对话（单图深挖）
        
        Args:
            photo_id: 照片ID
            analysis_result: 照片分析结果
            
        Returns:
            初始问题列表
        """
        self.current_photo_id = photo_id
        self.analysis_result = analysis_result
        self.qa_history = []
        
        # 生成初始问题
        from src.question_generator import QuestionGenerator
        generator = QuestionGenerator()
        questions = generator.generate_initial_questions(analysis_result)
        
        return questions
    
    def add_answer(self, question: str, answer: str) -> Optional[str]:
        """
        添加用户回答，生成后续问题
        
        Args:
            question: 问题
            answer: 用户回答
            
        Returns:
            下一个问题（如果还有的话），否则返回None
        """
        # 保存问答对
        self.qa_history.append({
            "question": question,
            "answer": answer
        })
        
        # 检查是否达到最大轮数
        if len(self.qa_history) >= self.max_rounds:
            return None
        
        # 生成后续问题
        from src.question_generator import QuestionGenerator
        generator = QuestionGenerator()
        
        next_question = generator.generate_followup_question(
            self.analysis_result,
            self.qa_history
        )
        
        # 如果无法生成问题，返回None（不进行追问）
        if not next_question or not next_question.strip():
            return None
        
        return next_question
    
    def get_dialogue_summary(self) -> Dict:
        """
        获取对话摘要
        
        Returns:
            包含照片信息和对话历史的字典
        """
        return {
            "photo_id": self.current_photo_id,
            "analysis": self.analysis_result,
            "qa_history": self.qa_history,
            "rounds": len(self.qa_history)
        }
    
    def reset(self):
        """重置对话管理器"""
        self.current_photo_id = None
        self.analysis_result = None
        self.qa_history = []
