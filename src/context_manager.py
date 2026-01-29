"""
多图上下文管理模块
实现跨图片的记忆管理，确保连贯的长篇叙事
"""
from typing import Dict, List, Optional
import json
import os
from datetime import datetime
import chromadb
from chromadb.config import Settings
import config


class ContextManager:
    """多图上下文管理器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化上下文管理器
        
        Args:
            db_path: 向量数据库路径
        """
        self.db_path = db_path or config.VECTOR_DB_PATH
        os.makedirs(self.db_path, exist_ok=True)
        
        # 初始化向量数据库
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 创建或获取集合
        self.collection = self.client.get_or_create_collection(
            name="photo_stories",
            metadata={"description": "照片故事上下文存储"}
        )
        
        # 内存中的照片序列
        self.photo_sequence: List[Dict] = []
    
    def add_photo_dialogue(
        self,
        photo_id: str,
        analysis_result: Dict,
        qa_history: List[Dict]
    ) -> str:
        """
        添加一张照片的对话记录
        
        Args:
            photo_id: 照片ID
            analysis_result: 照片分析结果
            qa_history: 问答历史
            
        Returns:
            记录ID
        """
        # 构建文档内容
        dialogue_text = self._format_dialogue(analysis_result, qa_history)
        
        # 提取关键信息（人物、地点、事件等）
        key_info = self._extract_key_info(analysis_result, qa_history)
        
        # 创建记录
        record = {
            "photo_id": photo_id,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis_result,
            "qa_history": qa_history,
            "key_info": key_info,
            "dialogue_text": dialogue_text
        }
        
        # 添加到序列
        self.photo_sequence.append(record)
        
        # 存储到向量数据库
        record_id = f"photo_{photo_id}_{len(self.photo_sequence)}"
        self.collection.add(
            documents=[dialogue_text],
            metadatas=[{
                "photo_id": photo_id,
                "key_info": json.dumps(key_info, ensure_ascii=False),
                "sequence": len(self.photo_sequence)
            }],
            ids=[record_id]
        )
        
        return record_id
    
    def get_relevant_context(
        self,
        current_analysis: Dict,
        top_k: int = 3
    ) -> Dict:
        """
        获取与当前照片相关的上下文
        
        Args:
            current_analysis: 当前照片的分析结果
            top_k: 返回最相关的k条记录
            
        Returns:
            相关上下文信息
        """
        if len(self.photo_sequence) == 0:
            return {}
        
        # 构建查询文本
        query_text = current_analysis.get('overall_description', '')
        
        # 从向量数据库检索
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(top_k, len(self.photo_sequence))
        )
        
        # 提取相关信息
        relevant_context = {
            "previous_photos": [],
            "key_connections": []
        }
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for i, record_id in enumerate(results['ids'][0]):
                # 从序列中查找对应记录
                seq_num = int(results['metadatas'][0][i].get('sequence', 0)) - 1
                if 0 <= seq_num < len(self.photo_sequence):
                    record = self.photo_sequence[seq_num]
                    relevant_context["previous_photos"].append({
                        "photo_id": record["photo_id"],
                        "key_info": record["key_info"],
                        "summary": record["dialogue_text"][:200] + "..."
                    })
        
        # 如果没有检索到，使用最近的记录
        if not relevant_context["previous_photos"] and len(self.photo_sequence) > 0:
            last_record = self.photo_sequence[-1]
            relevant_context["previous_photos"].append({
                "photo_id": last_record["photo_id"],
                "key_info": last_record["key_info"],
                "summary": last_record["dialogue_text"][:200] + "..."
            })
        
        return relevant_context
    
    def generate_cross_photo_question(
        self,
        current_analysis: Dict
    ) -> Optional[str]:
        """
        生成跨照片的关联问题
        
        Args:
            current_analysis: 当前照片的分析结果
            
        Returns:
            关联性问题（如果有相关上下文），否则返回None
        """
        if len(self.photo_sequence) == 0:
            return None
        
        # 获取相关上下文
        context = self.get_relevant_context(current_analysis, top_k=1)
        
        if not context.get("previous_photos"):
            return None
        
        # 使用上一张照片的信息
        previous_photo = self.photo_sequence[-1]
        
        from src.question_generator import QuestionGenerator
        generator = QuestionGenerator()
        
        prev_analysis = previous_photo["analysis"] or {}
        question = generator.generate_cross_photo_question(
            current_analysis=current_analysis,
            previous_photo_info={
                "analysis": prev_analysis,
                "key_info": previous_photo["key_info"],
                "overall_description": prev_analysis.get("overall_description", ""),
            },
            previous_qa=previous_photo["qa_history"]
        )
        
        return question
    
    def _format_dialogue(self, analysis_result: Dict, qa_history: List[Dict]) -> str:
        """格式化对话为文本"""
        text_parts = [
            f"照片描述：{analysis_result.get('overall_description', '')}"
        ]
        
        for qa in qa_history:
            text_parts.append(f"问：{qa.get('question', '')}")
            text_parts.append(f"答：{qa.get('answer', '')}")
        
        return "\n".join(text_parts)
    
    def _extract_key_info(
        self,
        analysis_result: Dict,
        qa_history: List[Dict]
    ) -> Dict:
        """
        提取关键信息（人物、地点、事件、时间等）
        
        Args:
            analysis_result: 照片分析结果
            qa_history: 问答历史
            
        Returns:
            关键信息字典
        """
        key_info = {
            "people": [],
            "places": [],
            "events": [],
            "time": None,
            "emotions": []
        }
        
        # 从问答中提取关键信息（简化版，实际可以使用NER模型）
        all_text = analysis_result.get('overall_description', '') + " " + \
                   " ".join([qa.get('answer', '') for qa in qa_history])
        
        # 简单的关键词提取（实际应该使用更高级的NLP方法）
        # 这里只是示例，实际应该使用NER或信息抽取模型
        
        return key_info
    
    def get_story_timeline(self) -> List[Dict]:
        """
        获取故事时间线
        
        Returns:
            按时间顺序的照片记录列表
        """
        return self.photo_sequence.copy()
    
    def clear(self):
        """清空所有上下文"""
        self.photo_sequence = []
        # 清空向量数据库
        self.client.delete_collection(name="photo_stories")
        self.collection = self.client.get_or_create_collection(
            name="photo_stories",
            metadata={"description": "照片故事上下文存储"}
        )
