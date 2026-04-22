"""
多图上下文管理模块
实现跨图片的记忆管理，确保连贯的长篇叙事
"""
from typing import Dict, List, Optional
import json
import os
import re
from datetime import datetime
import chromadb
from chromadb.config import Settings
import config


class ContextManager:
    """多图上下文管理器"""

    PERSON_KEYWORDS = [
        "我", "父亲", "母亲", "爸爸", "妈妈", "爷爷", "奶奶", "外公", "外婆",
        "叔叔", "阿姨", "老师", "同学", "战友", "连长", "指导员", "妻子", "丈夫",
        "儿子", "女儿", "孙子", "孙女", "哥哥", "姐姐", "弟弟", "妹妹"
    ]
    PLACE_KEYWORDS = [
        "老家", "家里", "村里", "学校", "部队", "工厂", "县城", "镇上", "南澳岛",
        "广州", "汕头", "东莞", "福建", "广东", "车间", "营房", "祠堂", "宗祠"
    ]
    EVENT_KEYWORDS = [
        "参军", "入伍", "退伍", "转业", "上学", "毕业", "结婚", "生孩子", "比赛",
        "演讲", "下乡", "返城", "工作", "退休", "修祠", "建桥", "拍照", "获奖"
    ]
    EMOTION_KEYWORDS = [
        "高兴", "开心", "难过", "激动", "紧张", "骄傲", "怀念", "感动", "遗憾", "委屈", "自豪"
    ]
    
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
            "sequence": len(self.photo_sequence) + 1,
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
                "sequence": len(self.photo_sequence),
                "stage": key_info.get("stage") or "unknown"
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
        query_text = self._build_query_text(current_analysis)
        
        # 从向量数据库检索
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(top_k, len(self.photo_sequence))
        )
        
        # 提取相关信息
        relevant_context = {
            "previous_photos": [],
            "key_connections": [],
            "latest_photo": None,
            "retrieved_photo": None,
            "merged_key_info": {
                "people": [],
                "places": [],
                "events": [],
                "time": None,
                "emotions": [],
                "stage": None,
            }
        }
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for i, record_id in enumerate(results['ids'][0]):
                # 从序列中查找对应记录
                seq_num = int(results['metadatas'][0][i].get('sequence', 0)) - 1
                if 0 <= seq_num < len(self.photo_sequence):
                    record = self.photo_sequence[seq_num]
                    relevant_context["previous_photos"].append({
                        "photo_id": record["photo_id"],
                        "sequence": record["sequence"],
                        "record_index": seq_num,
                        "key_info": record["key_info"],
                        "summary": record["dialogue_text"][:200] + "..."
                    })
        
        # 如果没有检索到，使用最近的记录
        if not relevant_context["previous_photos"] and len(self.photo_sequence) > 0:
            last_record = self.photo_sequence[-1]
            relevant_context["previous_photos"].append({
                "photo_id": last_record["photo_id"],
                "sequence": last_record["sequence"],
                "record_index": len(self.photo_sequence) - 1,
                "key_info": last_record["key_info"],
                "summary": last_record["dialogue_text"][:200] + "..."
            })

        if self.photo_sequence:
            latest_record = self.photo_sequence[-1]
            relevant_context["latest_photo"] = {
                "photo_id": latest_record["photo_id"],
                "sequence": latest_record["sequence"],
                "record_index": len(self.photo_sequence) - 1,
                "key_info": latest_record["key_info"],
                "summary": latest_record["dialogue_text"][:200] + "..."
            }

        if relevant_context["previous_photos"]:
            relevant_context["retrieved_photo"] = relevant_context["previous_photos"][0]
            relevant_context["merged_key_info"] = self._merge_key_info(
                [entry.get("key_info", {}) for entry in relevant_context["previous_photos"]]
            )
            relevant_context["key_connections"] = self._build_key_connections(
                relevant_context["previous_photos"]
            )
        
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
        
        previous_photo = self._select_reference_record(context)
        if previous_photo is None:
            return None
        
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

    def _build_query_text(self, analysis_result: Dict) -> str:
        """构建更适合检索的查询文本。"""
        parts = [
            str(analysis_result.get("overall_description", "") or ""),
            str(analysis_result.get("background", "") or ""),
            str(analysis_result.get("emotions", "") or ""),
            str(analysis_result.get("era_items", "") or ""),
        ]
        return " ".join(part for part in parts if part).strip()
    
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
            "emotions": [],
            "stage": None,
        }
        
        text_parts = [
            str(analysis_result.get("overall_description", "") or ""),
            str(analysis_result.get("background", "") or ""),
            str(analysis_result.get("emotions", "") or ""),
            str(analysis_result.get("clothing", "") or ""),
            str(analysis_result.get("era_items", "") or ""),
            " ".join(qa.get("question", "") for qa in qa_history),
            " ".join(qa.get("answer", "") for qa in qa_history),
        ]
        all_text = " ".join(part for part in text_parts if part)

        key_info["people"] = self._extract_keyword_hits(all_text, self.PERSON_KEYWORDS)
        key_info["places"] = self._extract_places(all_text)
        key_info["events"] = self._extract_events(all_text)
        key_info["time"] = self._extract_time(all_text)
        key_info["emotions"] = self._extract_emotions(all_text)
        key_info["stage"] = self._infer_stage(all_text)
        
        return key_info

    def _extract_keyword_hits(self, text: str, keywords: List[str]) -> List[str]:
        hits = []
        for keyword in keywords:
            if keyword in text and keyword not in hits:
                hits.append(keyword)
        return hits[:6]

    def _extract_places(self, text: str) -> List[str]:
        places = self._extract_keyword_hits(text, self.PLACE_KEYWORDS)
        regex_hits = re.findall(r"([\u4e00-\u9fff]{2,10}(?:村|镇|县|市|岛|山|海|厂|校|营|祠|堂))", text)
        for place in regex_hits:
            if place not in places:
                places.append(place)
        return places[:6]

    def _extract_events(self, text: str) -> List[str]:
        events = self._extract_keyword_hits(text, self.EVENT_KEYWORDS)
        snippets = re.findall(
            r"([\u4e00-\u9fff0-9]{0,8}(?:参军|入伍|退伍|转业|上学|毕业|结婚|退休|比赛|演讲|下乡|返城|修祠|拍照)[\u4e00-\u9fff0-9]{0,8})",
            text,
        )
        for snippet in snippets:
            cleaned = snippet.strip(" ，。；：")
            if cleaned and cleaned not in events:
                events.append(cleaned)
        return events[:6]

    def _extract_time(self, text: str) -> Optional[str]:
        patterns = [
            r"(\d{4}年)",
            r"((?:19|20)\d{2}年代)",
            r"(小时候|童年|青年时期|年轻时|晚年|退休后)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    def _extract_emotions(self, text: str) -> List[str]:
        emotions = self._extract_keyword_hits(text, self.EMOTION_KEYWORDS)
        if not emotions:
            regex_hits = re.findall(r"(很(?:高兴|开心|难过|激动|紧张|骄傲|怀念|感动|遗憾|自豪))", text)
            for emotion in regex_hits:
                if emotion not in emotions:
                    emotions.append(emotion)
        return emotions[:5]

    def _infer_stage(self, text: str) -> Optional[str]:
        rules = [
            ("童年", ["小时候", "童年", "上小学"]),
            ("求学", ["读书", "上学", "毕业", "学校"]),
            ("军旅", ["参军", "入伍", "部队", "战友", "连长"]),
            ("工作", ["工作", "工厂", "单位", "车间", "演讲", "比赛"]),
            ("家庭", ["结婚", "孩子", "一家人", "父亲", "母亲"]),
            ("晚年", ["退休", "晚年", "孙子", "孙女"]),
        ]
        for stage, keywords in rules:
            if any(keyword in text for keyword in keywords):
                return stage
        return None

    def _merge_key_info(self, key_infos: List[Dict]) -> Dict:
        merged = {
            "people": [],
            "places": [],
            "events": [],
            "time": None,
            "emotions": [],
            "stage": None,
        }
        for key_info in key_infos:
            for field in ("people", "places", "events", "emotions"):
                for item in key_info.get(field, []) or []:
                    if item and item not in merged[field]:
                        merged[field].append(item)
            if not merged["time"] and key_info.get("time"):
                merged["time"] = key_info["time"]
            if not merged["stage"] and key_info.get("stage"):
                merged["stage"] = key_info["stage"]
        return merged

    def _build_key_connections(self, previous_photos: List[Dict]) -> List[str]:
        if not previous_photos:
            return []
        merged = self._merge_key_info([entry.get("key_info", {}) for entry in previous_photos])
        connections = []
        if merged["people"]:
            connections.append(f"重复出现的人物线索：{'、'.join(merged['people'][:3])}")
        if merged["places"]:
            connections.append(f"可延续的地点线索：{'、'.join(merged['places'][:3])}")
        if merged["events"]:
            connections.append(f"前文事件线索：{'、'.join(merged['events'][:3])}")
        if merged.get("stage"):
            connections.append(f"当前最相关的人生阶段：{merged['stage']}")
        return connections[:4]

    def _select_reference_record(self, context: Dict) -> Optional[Dict]:
        if not context:
            return self.photo_sequence[-1] if self.photo_sequence else None

        retrieved = context.get("retrieved_photo")
        if retrieved is not None:
            record_index = retrieved.get("record_index")
            if isinstance(record_index, int) and 0 <= record_index < len(self.photo_sequence):
                return self.photo_sequence[record_index]

        latest = context.get("latest_photo")
        if latest is not None:
            record_index = latest.get("record_index")
            if isinstance(record_index, int) and 0 <= record_index < len(self.photo_sequence):
                return self.photo_sequence[record_index]

        return self.photo_sequence[-1] if self.photo_sequence else None
    
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
