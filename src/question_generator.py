"""
问题生成模块
基于视觉理解生成针对性的访谈问题
"""
from typing import Dict, List, Optional
import config


class QuestionGenerator:
    """访谈问题生成器"""
    
    def __init__(self, api_key: str = None, api_endpoint: str = None):
        """
        初始化问题生成器
        
        Args:
            api_key: 混元API密钥
            api_endpoint: API端点
        """
        self.api_key = api_key or config.HUNYUAN_API_KEY
        self.api_endpoint = api_endpoint or config.HUNYUAN_API_ENDPOINT
    
    def generate_initial_questions(
        self, 
        analysis_result: Dict,
        context: Optional[Dict] = None
    ) -> List[str]:
        """
        基于照片分析结果生成初始访谈问题
        
        Args:
            analysis_result: 多模态分析结果
            context: 可选的上下文信息（用于多图场景）
            
        Returns:
            问题列表
        """
        # 构建问题生成提示词
        prompt = self._build_question_prompt(analysis_result, context, is_initial=True)
        
        # 调用API生成问题
        questions_text = self._call_api_for_questions(prompt)
        
        # 解析问题列表（传递分析结果以便备用生成）
        questions = self._parse_questions(questions_text, analysis_result)
        
        # 如果无法提取问题，尝试更激进的方法
        if not questions:
            # 尝试直接查找所有包含问号的句子（仅保留中文）
            questions = self._extract_any_questions(questions_text, analysis_result)
        
        # 如果还是无法提取，基于分析结果直接生成问题
        if not questions:
            print(f"[提示] 无法从API响应中提取问题，基于照片分析结果生成问题...")
            questions = self._generate_questions_from_analysis(analysis_result)
        
        return questions[:5] if questions else []
    
    def generate_followup_question(
        self,
        analysis_result: Dict,
        previous_qa: List[Dict],
        context: Optional[Dict] = None
    ) -> str:
        """
        基于之前的问答生成后续问题
        
        Args:
            analysis_result: 当前照片的分析结果
            previous_qa: 之前的问答对列表 [{"question": "...", "answer": "..."}]
            context: 可选的上下文信息
            
        Returns:
            后续问题
        """
        prompt = self._build_followup_prompt(analysis_result, previous_qa, context)
        raw_question = self._call_api_for_questions(prompt, single=True)
        
        # 过滤思考过程，提取实际问题
        question = self._parse_single_question(raw_question)
        
        return question
    
    def generate_cross_photo_question(
        self,
        current_analysis: Dict,
        previous_photo_info: Dict,
        previous_qa: List[Dict]
    ) -> str:
        """
        生成跨照片的关联问题（多图叙事链）
        
        Args:
            current_analysis: 当前照片的分析结果
            previous_photo_info: 上一张照片的信息（包括分析和访谈内容）
            previous_qa: 上一张照片的问答对
            
        Returns:
            关联性问题
        """
        prompt = f"""基于以下信息，生成一个能够连接两张照片的访谈问题：

上一张照片信息：
{previous_photo_info.get('overall_description', '')}
上一张照片的关键访谈内容：
{self._summarize_qa(previous_qa)}

当前照片信息：
{current_analysis.get('overall_description', '')}

请生成一个问题，能够：
1. 引用上一张照片中提到的人物、地点或事件
2. 结合当前照片的视觉特征
3. 引导用户讲述两张照片之间的关联和故事

例如："这还是刚才提到的那位李叔叔吗？" 或 "这张照片是在你刚才说的那个老房子附近拍的吗？"

重要：必须用中文回答。只输出一个中文问题，不要输出任何思考过程、推理或英文内容。直接输出问题。"""
        
        raw_question = self._call_api_for_questions(prompt, single=True)
        question = self._parse_single_question(raw_question)
        return question if question else "这张照片和上一张之间有什么关联？"
    
    def _build_question_prompt(
        self, 
        analysis_result: Dict, 
        context: Optional[Dict],
        is_initial: bool = True
    ) -> str:
        """构建问题生成提示词"""
        # 提取分析结果中的关键信息
        visual_elements = analysis_result.get('visual_elements', '')
        emotions = analysis_result.get('emotions', '')
        clothing = analysis_result.get('clothing', '')
        background = analysis_result.get('background', '')
        era_items = analysis_result.get('era_items', '')
        overall_desc = analysis_result.get('overall_description', '')
        
        # 尝试从整体描述中提取人物信息
        people_info = ""
        if isinstance(overall_desc, str):
            # 查找人物相关信息
            if '人物' in overall_desc or '人' in overall_desc:
                # 尝试提取人物描述
                import re
                people_match = re.search(r'人物[：:](.*?)(?:\n|$)', overall_desc)
                if people_match:
                    people_info = people_match.group(1).strip()
        
        # 如果没有单独的人物信息，尝试从visual_elements中提取
        if not people_info and visual_elements:
            if isinstance(visual_elements, dict) and 'characters' in visual_elements:
                people_info = str(visual_elements['characters'])
            elif isinstance(visual_elements, str) and ('人物' in visual_elements or '人' in visual_elements):
                people_info = visual_elements
        
        base_prompt = f"""你是一个专业的访谈问题生成器。基于以下照片分析结果，生成5个具体、有针对性的中文访谈问题。

照片分析结果：
"""
        
        # 根据分析结果的内容，有选择地添加信息
        if people_info:
            base_prompt += f"- 人物信息：{people_info}\n"
        if background:
            base_prompt += f"- 背景环境：{background}\n"
        if emotions:
            base_prompt += f"- 人物表情/情感：{emotions}\n"
        if clothing:
            base_prompt += f"- 服饰细节：{clothing}\n"
        if era_items:
            base_prompt += f"- 时代特征/物品：{era_items}\n"
        if visual_elements and not people_info:
            base_prompt += f"- 视觉元素：{visual_elements}\n"
        if overall_desc:
            # 限制整体描述的长度
            desc_short = overall_desc[:300] if len(overall_desc) > 300 else overall_desc
            base_prompt += f"- 整体描述：{desc_short}\n"
        
        if context:
            base_prompt += f"\n上下文信息：{context}\n"
        
        base_prompt += """
要求：
1. 每个问题必须基于上述分析结果中的具体元素（人物、背景、表情、服饰等）
2. 问题要具体，能够引导用户回忆和讲述故事
3. 结合照片中的视觉细节（如"看照片背景里的老房子，那是你小时候住的地方吗？"）
4. 问题要有层次：从简单的事实确认到深层的情感回忆
5. 使用温暖、亲切的语气
6. 每个问题一行，用数字编号

示例（基于分析结果）：
- 如果分析提到"背景是老房子" → "看照片背景里的老房子，那是你小时候住的地方吗？"
- 如果分析提到"人物表情是微笑" → "照片中你的笑容很自然，当时发生了什么开心的事情吗？"
- 如果分析提到"80年代的服装" → "照片中你穿的衣服很有年代感，还记得当时穿这身衣服的场合吗？"

重要：直接输出问题列表，不要任何思考过程、解释或元信息。
格式如下（直接开始，不要任何前缀）：
1. 第一个问题（必须基于分析结果中的具体元素）
2. 第二个问题（必须基于分析结果中的具体元素）
3. 第三个问题（必须基于分析结果中的具体元素）
4. 第四个问题（必须基于分析结果中的具体元素）
5. 第五个问题（必须基于分析结果中的具体元素）

只输出中文问题，每个问题一行，用数字编号。"""
        
        return base_prompt
    
    def _build_followup_prompt(
        self,
        analysis_result: Dict,
        previous_qa: List[Dict],
        context: Optional[Dict]
    ) -> str:
        """构建后续问题生成提示词"""
        qa_summary = self._summarize_qa(previous_qa)
        
        prompt = f"""基于以下信息，生成一个深入的后续访谈问题：

照片信息：
{analysis_result.get('overall_description', '')}

之前的问答：
{qa_summary}
"""
        
        if context:
            prompt += f"\n上下文：{context}\n"
        
        prompt += """
要求：
1. 基于用户之前的回答，提出更深入的问题
2. 可以追问细节、情感、背景故事
3. 避免重复之前的问题
4. 使用自然、对话式的语气

重要：直接输出一个问题，不要任何思考过程、解释或元信息。
直接开始输出问题，格式如下（不要任何前缀）：
[直接输出中文问题]

只输出中文问题，不要其他内容。"""
        
        return prompt
    
    def _summarize_qa(self, qa_list: List[Dict]) -> str:
        """总结问答对"""
        summary = []
        for i, qa in enumerate(qa_list, 1):
            summary.append(f"Q{i}: {qa.get('question', '')}")
            summary.append(f"A{i}: {qa.get('answer', '')}")
        return "\n".join(summary)
    
    def _call_api_for_questions(self, prompt: str, single: bool = False) -> str:
        """
        调用API生成问题（支持Gemini和混元）
        
        Args:
            prompt: 提示词
            single: 是否只生成单个问题
            
        Returns:
            生成的问题文本
        """
        # 检查是否使用Gemini API
        if config.USE_GEMINI:
            return self._call_gemini_text_api(prompt)
        else:
            return self._call_hunyuan_text_api(prompt, single)
    
    def _call_gemini_text_api(self, prompt: str) -> str:
        """调用Gemini API生成文本（优先使用 Google AI 官方格式）"""
        import requests
        
        model_name = getattr(config, "GEMINI_MODEL_NAME", "gemini-2.5-pro")
        payload_gemini = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": config.TEMPERATURE,
                "maxOutputTokens": 2048,
            },
        }
        last_error = None
        base = (self.api_endpoint or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")

        # 1. 优先：Google AI 官方 endpoint（generativelanguage.googleapis.com）
        if "generativelanguage.googleapis.com" in base:
            official_url = f"{base}/models/{model_name}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            }
            try:
                response = requests.post(
                    official_url,
                    headers=headers,
                    json=payload_gemini,
                    timeout=30,
                )
                response.raise_for_status()
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if parts and "text" in parts[0]:
                            return parts[0]["text"]
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:200] if e.response.text else str(e)}"
            except Exception as e:
                last_error = str(e)

        # 2. 其他 endpoint：OpenAI 兼容或 Bearer + Gemini 体
        headers_bearer = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload_openai = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config.TEMPERATURE,
        }
        endpoints_to_try = [
            (f"{base}/chat/completions", payload_openai, "choices"),
            (f"{base}/v1/chat/completions", payload_openai, "choices"),
            (f"{base}/models/{model_name}:generateContent", payload_gemini, "candidates"),
            (base, payload_gemini, "candidates"),
        ]
        for endpoint, payload, key in endpoints_to_try:
            if not endpoint or "generativelanguage.googleapis.com" in endpoint:
                continue
            try:
                resp = requests.post(
                    endpoint,
                    headers=headers_bearer,
                    json=payload,
                    timeout=30,
                )
                resp.raise_for_status()
                result = resp.json()
                if key == "choices" and "choices" in result and result["choices"]:
                    return result["choices"][0]["message"]["content"]
                if key == "candidates" and "candidates" in result and result["candidates"]:
                    c = result["candidates"][0]
                    if "content" in c and "parts" in c["content"] and c["content"]["parts"]:
                        return c["content"]["parts"][0].get("text", "")
                if "text" in result:
                    return result["text"]
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:200] if e.response.text else str(e)}"
            except Exception as e:
                last_error = str(e)

        if last_error:
            print(f"警告: 所有API格式尝试都失败，使用模拟数据。最后错误: {last_error}")
        else:
            print("警告: 所有API格式尝试都失败，使用模拟数据")
        return self._get_mock_questions(False)
    
    def _call_hunyuan_text_api(self, prompt: str, single: bool = False) -> str:
        """调用混元API生成文本（原始实现）"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "hunyuan-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": config.TEMPERATURE
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return self._get_mock_questions(single)
                
        except Exception as e:
            print(f"混元API调用错误: {e}")
            return self._get_mock_questions(single)
    
    def _parse_questions(self, questions_text: str, analysis_result: Dict = None) -> List[str]:
        """解析问题文本，提取问题列表，过滤思考过程"""
        import re
        
        # 首先尝试过滤思考过程
        cleaned_text = self._filter_thinking_process(questions_text)
        
        lines = cleaned_text.strip().split('\n')
        questions = []
        
        for line in lines:
            line = line.strip()
            
            # 跳过明显的思考过程标记
            if self._is_thinking_line(line):
                continue
            
            # 移除编号（如 "1. " 或 "1、"）
            line = re.sub(r'^\d+[\.、]\s*', '', line)
            
            # 移除Markdown格式标记（更彻底）
            line = re.sub(r'^\*\*.*?\*\*\s*', '', line)
            line = re.sub(r'^#+\s*', '', line)
            line = re.sub(r'\*\*.*?\*\*', '', line)  # 移除行中的 **标记**
            
            # 检查是否是有效问题
            if line and len(line) > 5:
                # 优先选择包含问号的行
                if '?' in line or '？' in line:
                    # 确保不是思考过程
                    if not self._is_thinking_line(line):
                        questions.append(line)
                # 或者看起来像问题的行（中文，长度合理）
                elif self._looks_like_question(line):
                    questions.append(line)
        
        # 如果解析失败，尝试从原始文本中提取（更激进的方法）
        if not questions:
            questions = self._extract_questions_aggressive(questions_text)
        
        # 如果还是没有问题，尝试从思考过程中提取问题
        if not questions:
            questions = self._extract_questions_from_thinking(questions_text)
        
        # 如果还是没有，使用最激进的方法（传递分析结果）
        if not questions:
            questions = self._extract_any_questions(questions_text, analysis_result)
        
        return questions[:5] if questions else []
    
    def _is_mostly_thinking_process(self, text: str) -> bool:
        """判断整个响应是否主要是思考过程"""
        lines = text.strip().split('\n')
        thinking_lines = 0
        total_lines = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            total_lines += 1
            if self._is_thinking_line(line):
                thinking_lines += 1
        
        # 如果超过70%的行是思考过程，认为整个响应都是思考过程
        if total_lines > 0 and thinking_lines / total_lines > 0.7:
            return True
        
        # 检查是否包含大量英文思考过程标记
        thinking_markers = ["I'm", "I've", "**Formulating", "**Crafting", "**Analyzing"]
        marker_count = sum(1 for marker in thinking_markers if marker in text)
        if marker_count >= 3:  # 包含3个或更多思考过程标记
            return True
        
        return False
    
    def _filter_thinking_process(self, text: str) -> str:
        """过滤掉思考过程（含英文推理句）"""
        import re
        
        # 移除明显的思考过程标记
        thinking_patterns = [
            r'\*\*[^*]+\*\*',  # **标题**
            r'I\'m\s+.*?\.',  # I'm ...
            r'I\'ve\s+.*?\.',  # I've ...
            r'Now I\'m\s+.*?\.',  # Now I'm ...
            r'I am\s+.*?\.',  # I am ...
            r'I have\s+.*?\.',  # I have ...
            r'How can I\s+.*?[.?]',  # How can I ...
            r'I\'m leaning\s+.*?[.?]',  # I'm leaning ...
            r'leaning towards\s+.*?[.?]',  # leaning towards ...
            r'我正在.*?。',  # 我正在...
            r'我已经.*?。',  # 我已经...
            r'现在.*?。',  # 现在...
        ]
        
        cleaned = text
        for pattern in thinking_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        
        return cleaned
    
    def _is_thinking_line(self, line: str) -> bool:
        """判断是否是思考过程行（含英文推理句）"""
        thinking_indicators = [
            "I'm", "I've", "Now I'm", "I am", "I have",
            "**Analyzing", "**Formulating", "**Crafting",
            "**Evaluating", "**Synthesizing", "**Defining",
            "**Designing", "**Planning", "**Refining",
            "**Targeted", "**Comprehending", "**Integrating",
            "我正在", "我已经", "现在", "接下来",
            "Crafting", "Designing", "Formulating", "currently",
            "stemming from", "I'm currently", "I've been",
            "how can I", "I'm leaning", "leaning towards",
            "visual paradox", "relationship between", "weave",
        ]
        
        line_lower = line.lower()
        
        # 如果行以 ** 开头，很可能是思考过程标题
        if line.strip().startswith('**'):
            return True
        
        # 检查是否包含思考过程标记
        if any(indicator.lower() in line_lower for indicator in thinking_indicators):
            return True
        
        # 如果行主要是英文且包含 "I'm", "I've" 等，很可能是思考过程
        if any(word in line_lower for word in ["i'm", "i've", "i am", "i have"]):
            chinese_chars = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
            if chinese_chars < len(line) * 0.3:  # 中文少于30%，很可能是思考过程
                return True
        
        # 整句主要为英文且不含问号，视为推理/思考
        chinese_chars = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
        if chinese_chars < len(line) * 0.2 and "?" not in line and "？" not in line:
            return True
        
        return False
    
    def _looks_like_question(self, line: str) -> bool:
        """判断是否看起来像问题"""
        # 包含问号
        if '?' in line or '？' in line:
            return True
        
        # 中文问题常见结尾
        question_endings = ['吗', '呢', '什么', '哪里', '何时', '如何', '为什么']
        if any(line.endswith(ending) for ending in question_endings):
            return True
        
        # 长度合理且主要是中文
        if 10 <= len(line) <= 100:
            chinese_chars = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
            if chinese_chars > len(line) * 0.5:  # 至少50%是中文
                return True
        
        return False
    
    def _extract_questions_aggressive(self, text: str) -> List[str]:
        """激进提取方法：从文本中提取可能的问题"""
        import re
        
        # 查找包含问号的句子
        questions = re.findall(r'[^。！？]*[？?][^。！？]*', text)
        
        # 过滤掉思考过程
        filtered = []
        for q in questions:
            q = q.strip()
            # 移除思考过程标记
            q = re.sub(r'^\*\*.*?\*\*\s*', '', q)
            q = re.sub(r'\*\*.*?\*\*', '', q)
            if q and not self._is_thinking_line(q) and len(q) > 5:
                # 检查是否主要是中文
                chinese_chars = sum(1 for c in q if '\u4e00' <= c <= '\u9fff')
                if chinese_chars > len(q) * 0.3:  # 至少30%是中文
                    filtered.append(q)
        
        return filtered[:5]
    
    def _extract_questions_from_thinking(self, text: str) -> List[str]:
        """从思考过程中提取问题：查找包含问题关键词的句子"""
        import re
        
        # 查找可能包含问题的句子（即使没有问号）
        # 查找包含问题关键词的句子
        question_keywords = ['什么', '哪里', '何时', '如何', '为什么', '谁', '哪个', '多少']
        
        sentences = re.split(r'[。！\n]', text)
        questions = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 5:
                continue
            
            # 跳过明显的思考过程
            if self._is_thinking_line(sentence):
                continue
            
            # 检查是否包含问题关键词
            if any(keyword in sentence for keyword in question_keywords):
                # 移除思考过程标记
                sentence = re.sub(r'^\*\*.*?\*\*\s*', '', sentence)
                sentence = re.sub(r'\*\*.*?\*\*', '', sentence)
                
                # 检查是否主要是中文
                chinese_chars = sum(1 for c in sentence if '\u4e00' <= c <= '\u9fff')
                if chinese_chars > len(sentence) * 0.3:  # 至少30%是中文
                    # 如果没有问号，添加问号
                    if '?' not in sentence and '？' not in sentence:
                        sentence += '？'
                    questions.append(sentence)
        
        return questions[:5]
    
    def _extract_any_questions(self, text: str, analysis_result: Dict = None) -> List[str]:
        """最激进的提取方法：从文本中提取任何可能的问题，即使包含思考过程"""
        import re
        
        questions = []
        
        # 方法1: 查找所有包含问号的句子
        question_sentences = re.findall(r'[^。！？\n]*[？?][^。！？\n]*', text)
        for q in question_sentences:
            q = q.strip()
            if q and len(q) > 5:
                # 移除所有Markdown标记
                q = re.sub(r'\*\*.*?\*\*', '', q)
                q = re.sub(r'^#+\s*', '', q)
                q = re.sub(r'^\d+[\.、]\s*', '', q)
                q = q.strip()
                if q:
                    # 检查是否主要是中文
                    chinese_chars = sum(1 for c in q if '\u4e00' <= c <= '\u9fff')
                    if chinese_chars > len(q) * 0.2:  # 至少20%是中文
                        questions.append(q)
        
        # 方法2: 如果还没有找到，尝试按行分割，查找包含问题关键词的行
        if not questions:
            lines = text.split('\n')
            question_keywords = ['什么', '哪里', '何时', '如何', '为什么', '谁', '哪个', '多少', '吗', '呢']
            
            for line in lines:
                line = line.strip()
                if not line or len(line) < 5:
                    continue
                
                # 移除Markdown标记
                line = re.sub(r'\*\*.*?\*\*', '', line)
                line = re.sub(r'^#+\s*', '', line)
                line = re.sub(r'^\d+[\.、]\s*', '', line)
                line = line.strip()
                
                if line:
                    # 检查是否包含问题关键词
                    if any(keyword in line for keyword in question_keywords):
                        # 检查是否主要是中文
                        chinese_chars = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
                        if chinese_chars > len(line) * 0.2:  # 至少20%是中文
                            # 如果没有问号，添加问号
                            if '?' not in line and '？' not in line:
                                line += '？'
                            questions.append(line)
        
        # 方法3: 如果思考过程完全是英文，基于分析结果生成问题
        if not questions and analysis_result:
            # 检查是否主要是英文思考过程
            english_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            
            if english_chars > chinese_chars * 2:  # 主要是英文
                # 基于分析结果生成问题
                questions = self._generate_questions_from_analysis(analysis_result)
        
        return questions[:5] if questions else []
    
    def _generate_questions_from_analysis(self, analysis_result: Dict) -> List[str]:
        """基于分析结果直接生成问题"""
        questions = []
        
        # 提取分析结果中的关键信息
        visual_elements = str(analysis_result.get('visual_elements', ''))
        emotions = str(analysis_result.get('emotions', ''))
        clothing = str(analysis_result.get('clothing', ''))
        background = str(analysis_result.get('background', ''))
        era_items = str(analysis_result.get('era_items', ''))
        overall_desc = str(analysis_result.get('overall_description', ''))
        
        # 提取人物信息
        people_info = ""
        if '人物' in overall_desc or '人' in overall_desc:
            import re
            people_match = re.search(r'人物[：:](.*?)(?:\n|$)', overall_desc)
            if people_match:
                people_info = people_match.group(1).strip()
        
        if not people_info and visual_elements:
            if isinstance(analysis_result.get('visual_elements'), dict):
                people_info = str(analysis_result.get('visual_elements', {}).get('characters', ''))
            elif '人物' in visual_elements or '人' in visual_elements:
                people_info = visual_elements
        
        # 基于分析结果生成问题
        # 问题1: 基于人物信息
        if people_info and ('人' in people_info or '人物' in people_info):
            if '游戏' in overall_desc or '游戏截图' in overall_desc:
                questions.append("这张游戏截图中的角色是谁？")
            else:
                questions.append("照片中的人是谁？")
        elif people_info:
            questions.append(f"照片中的{people_info}，你们是什么关系？")
        else:
            questions.append("照片中的人是谁？")
        
        # 问题2: 基于背景
        if background:
            if '老房子' in background or '房子' in background:
                questions.append("看照片背景里的房子，那是你小时候住的地方吗？")
            elif '场景' in background or '环境' in background:
                questions.append(f"照片中的{background}，这是在什么地方拍的？")
            else:
                questions.append(f"照片的背景是{background}，这是在什么地方拍的？")
        else:
            questions.append("这张照片是在什么地方拍的？")
        
        # 问题3: 基于表情/情感
        if emotions:
            if '微笑' in emotions or '笑' in emotions:
                questions.append("照片中你的笑容很自然，当时发生了什么开心的事情吗？")
            elif '表情' in emotions:
                questions.append(f"照片中人物的表情是{emotions}，当时的心情如何？")
            else:
                questions.append(f"照片中人物的表情是{emotions}，当时发生了什么？")
        else:
            questions.append("当时的心情如何？")
        
        # 问题4: 基于服饰/时代特征
        if clothing:
            questions.append(f"照片中你穿的衣服很有特点，还记得当时穿这身衣服的场合吗？")
        elif era_items:
            questions.append(f"照片中的{era_items}很有年代感，还记得当时的情景吗？")
        else:
            questions.append("这张照片是什么时候拍的？")
        
        # 问题5: 基于整体描述
        if overall_desc:
            # 提取关键信息
            if '游戏' in overall_desc or '游戏截图' in overall_desc:
                questions.append("这个游戏场景给你留下了什么印象？")
            elif '合影' in overall_desc or '家庭' in overall_desc:
                questions.append("这张合影对你来说有什么特殊的意义？")
            else:
                questions.append("这张照片对你来说有什么特殊的意义？")
        else:
            questions.append("这张照片对你来说有什么特殊的意义？")
        
        return questions[:5]
    
    def _parse_single_question(self, question_text: str) -> str:
        """解析单个问题，过滤思考过程，只返回中文问题"""
        import re
        
        def is_mainly_chinese(s: str) -> bool:
            if not s:
                return False
            chinese_chars = sum(1 for c in s if '\u4e00' <= c <= '\u9fff')
            return chinese_chars >= len(s) * 0.5
        
        # 过滤思考过程
        cleaned_text = self._filter_thinking_process(question_text)
        
        lines = cleaned_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过思考过程行
            if self._is_thinking_line(line):
                continue
            
            # 移除Markdown格式标记
            line = re.sub(r'^\*\*.*?\*\*\s*', '', line)
            line = re.sub(r'\*\*.*?\*\*', '', line)
            line = re.sub(r'^#+\s*', '', line)
            
            # 只接受中文问题
            if line and len(line) > 5 and is_mainly_chinese(line):
                if '?' in line or '？' in line:
                    return line
                if self._looks_like_question(line):
                    return line
        
        # 如果解析失败，尝试从文本中提取问题（更激进，且只要中文）
        questions = self._extract_questions_aggressive(question_text)
        for q in questions:
            if is_mainly_chinese(q):
                return q
        
        # 最后，尝试从思考过程中提取问题（只要中文）
        questions = self._extract_questions_from_thinking(question_text)
        for q in questions:
            if is_mainly_chinese(q):
                return q
        
        return ""
    
    def _get_mock_questions(self, single: bool = False) -> str:
        """返回模拟问题（用于测试）"""
        if single:
            return "这张照片是在什么场合拍摄的？当时的心情如何？"
        else:
            return """1. 看照片背景里的老房子，那是你小时候住的地方吗？
2. 照片中的这些人都是谁？你们是什么关系？
3. 这张照片是什么时候拍的？还记得当时的情景吗？
4. 照片中你的表情很自然，当时发生了什么有趣的事情吗？
5. 这张照片对你来说有什么特殊的意义？"""
