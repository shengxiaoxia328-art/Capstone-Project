"""
故事生成模块
融合视觉描述与访谈内容，生成图文并茂的文章
支持多种叙事风格：个人叙事、名家叙事、知名回忆录叙事
"""
from typing import Dict, List, Optional, Callable
import config

# 叙事风格体系：用户可选的大类及对应提示词描述
NARRATIVE_STYLES = {
    "personal": {
        "name": "个人叙事风格",
        "description": "第一人称、口语化、亲切自然，像在跟朋友讲述自己的经历。",
        "prompt_extra": """
叙事风格要求（必须严格遵循）：
- 采用第一人称「我」的视角叙述
- 语言口语化、亲切自然，像在跟朋友聊天讲故事
- 适当保留口语感，可带轻微感慨或调侃
- 情感真挚、不刻意煽情，突出个人经历与感受
""",
    },
    "famous_writer": {
        "name": "名家叙事风格（如沈从文等）",
        "description": "文学性强、含蓄隽永、乡土气息、白描手法，类似沈从文式的笔调。",
        "prompt_extra": """
叙事风格要求（必须严格遵循）：
- 采用类似沈从文等名家的文学笔调：含蓄、隽永、留白
- 多用白描，少用直白抒情；用细节与场景说话
- 语言简洁干净，有乡土或怀旧气息，节奏舒缓
- 可第三人称或第一人称，整体偏文学化、可读性强
""",
    },
    "memoir": {
        "name": "知名回忆录叙事风格（如马斯克传、李飞飞传）",
        "description": "传记式、纪实感、有细节与转折，理性与情感并重。",
        "prompt_extra": """
叙事风格要求（必须严格遵循）：
- 采用知名回忆录/传记式写法：纪实、有细节、有因果与转折
- 理性与情感并重：既交代事实与背景，又有人物感受与选择
- 叙述清晰、结构分明，可带一点「回顾人生节点」的视角
- 语气稳重、有分量，类似《马斯克传》《李飞飞自传》等回忆录风格
""",
    },
}


class StoryGenerator:
    """故事生成器"""
    
    def __init__(self, api_key: str = None, api_endpoint: str = None):
        """
        初始化故事生成器
        
        Args:
            api_key: 混元API密钥
            api_endpoint: API端点
        """
        if api_key and api_endpoint:
            self.api_key, self.api_endpoint = api_key, api_endpoint
        elif config.USE_HUNYUAN:
            self.api_key = config.HUNYUAN_API_KEY
            self.api_endpoint = config.HUNYUAN_API_ENDPOINT
        else:
            self.api_key = config.GEMINI_API_KEY
            self.api_endpoint = config.GEMINI_API_ENDPOINT
    
    def generate_single_photo_story(
        self,
        photo_id: str,
        analysis_result: Dict,
        qa_history: List[Dict],
        narrative_style: Optional[str] = None,
        on_stream_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        生成单张照片的故事文章
        
        Args:
            photo_id: 照片ID
            analysis_result: 照片分析结果
            qa_history: 问答历史
            narrative_style: 叙事风格键名，如 "personal" / "famous_writer" / "memoir"，None 表示不指定
            on_stream_chunk: 可选，流式输出时每收到一段文本就调用此回调（用于前端实时显示）
            
        Returns:
            生成的故事文章
        """
        # 构建故事生成提示词（含叙事风格）
        prompt = self._build_story_prompt(
            analysis_result, qa_history, single_photo=True, narrative_style=narrative_style
        )
        
        # 调用API生成故事（支持流式时实时回调）
        raw_story = self._call_api_for_story(prompt, on_stream_chunk=on_stream_chunk)
        
        # 过滤思考过程
        story = self._filter_thinking_process(raw_story)
        # 移除 API 可能返回的 JSON、分析说明等非叙事内容
        story = self._strip_analysis_from_story(story)
        
        # 如果过滤后还是思考过程或为空，尝试更激进的方法
        if self._is_mostly_thinking_process(story) or not story.strip():
            print("[提示] 故事响应主要是思考过程，尝试更激进的提取...")
            story = self._extract_story_aggressive(raw_story)
            story = self._strip_analysis_from_story(story or "")
        
        # 若仍无有效叙事，用分析+访谈拼出故事（保证访谈回答被写进正文）
        if self._is_mostly_thinking_process(story) or not story.strip():
            print("[提示] 无法从API响应中提取故事，将根据访谈内容生成...")
            story = self._generate_story_from_analysis(analysis_result, qa_history)
        
        # 最终兜底：绝不返回空，否则前端“生成的故事”会空白
        if not story or not story.strip():
            story = self._generate_story_from_analysis(analysis_result, qa_history)
        return story
    
    def generate_multi_photo_story(
        self,
        photo_records: List[Dict]
    ) -> str:
        """
        生成多张照片的连贯故事文章
        
        Args:
            photo_records: 照片记录列表，每个记录包含analysis和qa_history
            
        Returns:
            生成的连贯故事文章
        """
        # 构建多图故事生成提示词
        prompt = self._build_multi_story_prompt(photo_records)
        
        # 调用API生成故事
        raw_story = self._call_api_for_story(prompt)
        
        # 过滤思考过程
        story = self._filter_thinking_process(raw_story)
        
        return story
    
    def _build_story_prompt(
        self,
        analysis_result: Dict,
        qa_history: List[Dict],
        single_photo: bool = True,
        narrative_style: Optional[str] = None
    ) -> str:
        """构建故事生成提示词；narrative_style 为 NARRATIVE_STYLES 的键名时注入对应风格要求。"""
        # 格式化问答内容
        qa_text = "\n".join([
            f"问：{qa.get('question', '')}\n答：{qa.get('answer', '')}"
            for qa in qa_history
        ])
        
        style_block = ""
        if narrative_style and narrative_style in NARRATIVE_STYLES:
            style_block = NARRATIVE_STYLES[narrative_style]["prompt_extra"]
        
        prompt = f"""请基于以下「照片视觉分析」和「访谈内容」撰写一篇照片故事文章。
{style_block}

【照片视觉分析】（仅作背景，不要大段复述）：
{analysis_result.get('overall_description', '')}

【访谈内容】（必须作为故事核心，把用户的回答写进故事）：
{qa_text}

重要要求：
1. 故事必须以用户在「访谈内容」里的回答为核心。把用户提到的人物、事件、感受、回忆写进正文，用第一人称或自然叙述呈现，不能只写照片画面描述。
2. 禁止输出任何 JSON、代码块、分析结构、「深度分析」「请看以下」等说明性文字；只输出可读的叙事文章。
3. 输出必须是「一段完整的话」：整篇故事写成一段或数段连贯的叙述，前后衔接自然，像在讲一个完整的小故事，不要分点、不要列表、不要小标题。
4. 文章结构：简短引入照片场景 → 结合用户回答展开背后的故事（重点）→ 结尾升华情感。
5. 字数 800-1200 字，语言自然、有感染力。

请直接输出文章正文，不要任何标题、前缀或说明。"""
        
        return prompt
    
    def _build_multi_story_prompt(self, photo_records: List[Dict]) -> str:
        """构建多图故事生成提示词"""
        photo_sections = []
        
        for i, record in enumerate(photo_records, 1):
            analysis = record.get('analysis', {})
            qa_history = record.get('qa_history', [])
            
            qa_text = "\n".join([
                f"问：{qa.get('question', '')}\n答：{qa.get('answer', '')}"
                for qa in qa_history
            ])
            
            section = f"""
第{i}张照片：
视觉描述：{analysis.get('overall_description', '')}
访谈内容：
{qa_text}
"""
            photo_sections.append(section)
        
        prompt = f"""请基于以下多张照片的视觉分析和访谈内容，撰写一篇连贯的"照片故事"文章，串联起跨越时间的人生故事。

{''.join(photo_sections)}

要求：
1. 文章要能够自然地连接多张照片，展现时间线和故事发展
2. 在描述每张照片时，要引用前一张照片中提到的人物、地点或事件，形成连贯的叙事
3. 突出照片之间的关联和变化（时间、人物、场景的变化）
4. 输出必须是「一段完整的话」：整篇文章写成连贯的叙述，段落之间衔接自然，像在讲一个完整的人生故事，不要分点、不要列表、不要小标题。
5. 文章结构：整体引入 → 按时间顺序描述每张照片及其故事 → 总结和升华
6. 字数控制在1500-2500字
7. 语言要温暖、有感染力，能够展现人生的变迁和情感的延续

重要：只输出文章内容，不要输出任何思考过程、解释、元信息或英文内容。
直接开始写文章，格式如下：

[文章内容直接开始，不要有任何前缀或说明]

请直接输出文章内容，不要添加标题或其他说明。"""
        
        return prompt
    
    def _filter_thinking_process(self, text: str) -> str:
        """过滤掉思考过程，提取实际的故事内容"""
        import re
        
        # 更彻底的思考过程模式
        thinking_patterns = [
            r'\*\*[^*]+\*\*\s*',  # **标题**
            r'I\'m\s+.*?\.',  # I'm ...
            r'I\'ve\s+.*?\.',  # I've ...
            r'Now I\'m\s+.*?\.',  # Now I'm ...
            r'I am\s+.*?\.',  # I am ...
            r'I have\s+.*?\.',  # I have ...
            r'My goal\s+.*?\.',  # My goal ...
            r'My plan\s+.*?\.',  # My plan ...
            r'Next, I\'ll\s+.*?\.',  # Next, I'll ...
            r'I\'ll focus\s+.*?\.',  # I'll focus ...
            r'I\'ll describe\s+.*?\.',  # I'll describe ...
            r'I\'ll begin\s+.*?\.',  # I'll begin ...
            r'Considering\s+.*?\.',  # Considering ...
            r'The goal is\s+.*?\.',  # The goal is ...
            r'我正在.*?。',  # 我正在...
            r'我已经.*?。',  # 我已经...
            r'现在.*?。',  # 现在...
        ]
        
        cleaned = text
        for pattern in thinking_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        
        # 移除整行思考过程
        lines = cleaned.split('\n')
        story_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 跳过思考过程标记行
            if self._is_thinking_line(line):
                continue
            
            # 跳过以思考过程开头的行
            thinking_starters = ['I\'m', 'I\'ve', 'I am', 'I have', 'My goal', 'My plan', 
                                'Next,', 'I\'ll', 'The goal', 'Considering', 'After analyzing']
            if any(line.startswith(starter) for starter in thinking_starters):
                continue
            
            # 检查是否主要是英文思考过程（没有实际故事内容）
            english_chars = sum(1 for c in line if c.isalpha() and ord(c) < 128)
            chinese_chars = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
            
            # 如果主要是英文且没有中文，很可能是思考过程
            if english_chars > chinese_chars * 3 and chinese_chars == 0:
                continue
            
            # 检查是否主要是中文（故事内容）
            if chinese_chars > len(line) * 0.3:  # 至少30%是中文
                story_lines.append(line)
            # 或者包含故事性词汇
            elif any(keyword in line for keyword in ['照片', '故事', '回忆', '时光', '那年', '那时', '记得', '想起']):
                story_lines.append(line)
        
        # 如果找到了故事内容，返回它
        if story_lines:
            story = '\n'.join(story_lines)
            # 再次清理，移除残留的思考过程标记
            story = re.sub(r'\*\*.*?\*\*', '', story)
            story = re.sub(r'^#+\s*', '', story, flags=re.MULTILINE)
            return story.strip()
        
        # 如果完全没有故事内容，返回空字符串（让调用者知道需要处理）
        return ""
    
    def _strip_analysis_from_story(self, text: str) -> str:
        """从故事文本中移除 JSON、分析说明等非叙事内容，只保留可读叙事。"""
        import re
        if not text or not text.strip():
            return text
        s = text
        # 移除 ```json ... ``` 或 ``` ... ``` 代码块
        s = re.sub(r'```json\s*[\s\S]*?```', '', s, flags=re.IGNORECASE)
        s = re.sub(r'```\s*[\s\S]*?```', '', s)
        # 移除 { "key": "value" } 形式的 JSON 块（跨行）
        s = re.sub(r'\{\s*"[^"]+"\s*:\s*[^{}]+\s*\}', '', s)
        s = re.sub(r'\{\s*"visual_elements"[^}]*\}', '', s, flags=re.DOTALL)
        # 移除典型分析/说明句（整句）
        analysis_phrases = [
            r'好的[，,]?\s*请看以下[^。]*?分析[。.]?',
            r'其画面精度[、,]?\s*光影效果[^。]*?指向了这一点[。.]?',
            r'这张图片并非[^。]*?电子游戏的截\s*图[。.]?',
            r'因此[，,]?\s*以下的分析将基于[^。]*?前提[。.]?',
            r'以下的分析将基于[^。]*?数字创作品的前提[。.]?',
        ]
        for pat in analysis_phrases:
            s = re.sub(pat, '', s, flags=re.IGNORECASE)
        # 按行过滤：丢弃明显是分析结构的行
        lines = s.split('\n')
        kept = []
        skip_keywords = ('visual_elements', 'expression_and_emotion', 'background_architecture', '"人物"', '"场景"', '"数量"', '"年龄"', '"性别"', '关系推测', '建筑风格', '人物表情', '姿态和情绪')
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if any(kw in line_stripped for kw in skip_keywords):
                continue
            if re.match(r'^\s*[\{\[]', line_stripped) or (line_stripped.startswith('"') and '":' in line_stripped):
                continue
            kept.append(line_stripped)
        s = '\n'.join(kept)
        s = re.sub(r'\n{3,}', '\n\n', s)
        s = re.sub(r' +', ' ', s)  # 仅合并空格，保留换行
        return s.strip()
    
    def _story_uses_qa(self, story: str, qa_history: List[Dict]) -> bool:
        """判断故事是否明显用到了访谈内容（至少包含某条回答中的片段）。"""
        if not story or not qa_history:
            return bool(qa_history)
        story_lower = story.strip()[:2000]
        for qa in qa_history:
            ans = (qa.get('answer') or '').strip()
            if len(ans) < 3:
                continue
            # 取回答的前 15 个字符作为片段，避免过长
            fragment = ans[:15] if len(ans) >= 15 else ans
            if fragment in story_lower:
                return True
        return False
    
    def _is_mostly_thinking_process(self, text: str) -> bool:
        """判断文本是否主要是思考过程"""
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
        
        # 如果超过70%的行是思考过程，认为主要是思考过程
        if total_lines > 0 and thinking_lines / total_lines > 0.7:
            return True
        
        # 检查是否包含大量英文思考过程标记
        thinking_markers = ["I'm", "I've", "My goal", "My plan", "Next, I'll", "I'll focus"]
        marker_count = sum(1 for marker in thinking_markers if marker in text)
        if marker_count >= 2:
            return True
        
        return False
    
    def _extract_story_aggressive(self, text: str) -> str:
        """激进的故事提取：从思考过程中提取故事内容"""
        import re
        
        # 方法1: 查找所有中文段落
        paragraphs = re.split(r'\n\n+', text)
        chinese_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 跳过明显的思考过程段落
            if self._is_thinking_line(para[:50]):  # 检查前50个字符
                continue
            
            # 检查中文比例
            chinese_chars = sum(1 for c in para if '\u4e00' <= c <= '\u9fff')
            if chinese_chars > len(para) * 0.3:  # 至少30%是中文
                # 移除Markdown标记
                para = re.sub(r'\*\*.*?\*\*', '', para)
                para = re.sub(r'#+\s*', '', para)
                para = para.strip()
                if para:
                    chinese_paragraphs.append(para)
        
        if chinese_paragraphs:
            return '\n\n'.join(chinese_paragraphs)
        
        # 方法2: 如果还是没有，尝试提取所有包含中文的句子
        sentences = re.split(r'[。！\n]', text)
        chinese_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
            
            # 跳过思考过程
            if self._is_thinking_line(sentence):
                continue
            
            # 检查中文比例
            chinese_chars = sum(1 for c in sentence if '\u4e00' <= c <= '\u9fff')
            if chinese_chars > len(sentence) * 0.2:  # 至少20%是中文
                # 移除Markdown标记
                sentence = re.sub(r'\*\*.*?\*\*', '', sentence)
                sentence = re.sub(r'#+\s*', '', sentence)
                sentence = sentence.strip()
                if sentence:
                    chinese_sentences.append(sentence)
        
        if chinese_sentences:
            return ' '.join(chinese_sentences[:10])  # 限制句子数量
        
        # 如果还是没有，返回空字符串（让调用者使用备用方法）
        return ""
    
    def _generate_story_from_analysis(self, analysis_result: Dict, qa_history: List[Dict]) -> str:
        """基于分析结果生成故事（当API返回思考过程时使用）"""
        import re
        import json
        
        # 提取分析结果中的关键信息
        overall_desc = str(analysis_result.get('overall_description', ''))
        visual_elements = analysis_result.get('visual_elements', '')
        emotions = str(analysis_result.get('emotions', ''))
        background = str(analysis_result.get('background', ''))
        clothing = str(analysis_result.get('clothing', ''))
        
        # 尝试从整体描述中提取结构化信息
        people_info = ""
        scene_info = ""
        emotion_info = ""
        
        # 清理描述文本（移除JSON标记等）
        if overall_desc:
            overall_desc = re.sub(r'```json\s*', '', overall_desc)
            overall_desc = re.sub(r'```\s*', '', overall_desc)
            overall_desc = overall_desc.strip()
            
            # 尝试解析JSON格式的描述
            try:
                if '{' in overall_desc and '}' in overall_desc:
                    json_match = re.search(r'\{.*\}', overall_desc, re.DOTALL)
                    if json_match:
                        desc_json = json.loads(json_match.group())
                        if isinstance(desc_json, dict):
                            # 提取人物信息
                            if '人物' in desc_json or '1. 视觉元素' in desc_json:
                                visual_data = desc_json.get('1. 视觉元素', desc_json.get('视觉元素', {}))
                                if isinstance(visual_data, dict) and '人物' in visual_data:
                                    people_data = visual_data['人物']
                                    if isinstance(people_data, dict):
                                        people_info = f"{people_data.get('数量', '')}，{people_data.get('身份推测', '')}"
                                    else:
                                        people_info = str(people_data)
                            
                            # 提取场景信息
                            if '场景' in desc_json or '背景' in desc_json:
                                scene_info = str(desc_json.get('场景', desc_json.get('背景', '')))
            except:
                pass
        
        # 如果无法从JSON提取，从文本中提取
        if not people_info:
            if isinstance(visual_elements, dict):
                if 'characters' in visual_elements:
                    people_info = str(visual_elements['characters'])
            elif isinstance(visual_elements, str):
                people_info = visual_elements
        
        # 构建流畅的故事
        story_parts = []
        
        # 开头 - 根据照片类型选择
        if '游戏' in overall_desc or '游戏截图' in overall_desc or '数字艺术' in overall_desc:
            story_parts.append("这是一张游戏截图，记录着那个时刻的精彩瞬间。")
        else:
            story_parts.append("这是一张珍贵的照片，记录着那个年代的温馨时光。")
        
        # 描述人物
        if people_info:
            if '游戏' in overall_desc or '角色' in people_info:
                story_parts.append(f"\n画面中，{people_info}站在这个奇幻世界的边缘。")
            elif '人' in people_info:
                story_parts.append(f"\n照片中，{people_info}。")
            else:
                story_parts.append(f"\n照片中的人物，{people_info}。")
        
        # 描述场景/背景
        if background:
            if '游戏' in overall_desc:
                story_parts.append(f"\n背景是一个宏大而奇异的超现实景观，{background}。")
            else:
                story_parts.append(f"\n照片的背景是{background}，")
        elif scene_info:
            story_parts.append(f"\n{scene_info}，")
        
        # 描述情绪/氛围
        if emotions:
            if '敬畏' in emotions or '惊奇' in emotions:
                story_parts.append(f"整个画面充满了{emotions}的氛围。")
            else:
                story_parts.append(f"从画面中可以感受到{emotions}。")
        
        # 描述整体场景
        if overall_desc and len(overall_desc) > 50:
            # 提取描述中的核心内容，避免重复
            desc_clean = overall_desc[:300]
            # 移除已经使用的信息
            if people_info and people_info in desc_clean:
                desc_clean = desc_clean.replace(people_info, '')
            if background and background in desc_clean:
                desc_clean = desc_clean.replace(background, '')
            desc_clean = desc_clean.strip()
            if desc_clean and len(desc_clean) > 20:
                story_parts.append(f"\n{desc_clean}。")
        
        # 以访谈回答为核心写故事（保证用户说的内容出现在正文里）
        if qa_history:
            story_parts.append("\n\n在访谈里，我分享了和这张照片有关的回忆：")
            for qa in qa_history[:5]:  # 最多 5 组问答
                q = (qa.get('question') or '').strip()
                a = (qa.get('answer') or '').strip()
                if not a or len(a) < 2:
                    continue
                # 把用户回答写成一句或一段叙述
                story_parts.append(f"\n{a}")
        
        # 结尾 - 根据照片类型选择
        if '游戏' in overall_desc or '游戏截图' in overall_desc:
            story_parts.append("\n\n这个游戏场景记录着一段虚拟世界的冒险，虽然并非真实，但同样承载着玩家的回忆和情感。")
        else:
            story_parts.append("\n\n这张照片承载着美好的回忆，值得珍藏。")
        
        # 组合故事，确保流畅
        story = ''.join(story_parts)
        
        # 清理多余的标点和空格
        story = re.sub(r'\s+', ' ', story)  # 多个空格合并为一个
        story = re.sub(r'，\s*，', '，', story)  # 多个逗号合并
        story = re.sub(r'。\s*。', '。', story)  # 多个句号合并
        story = story.strip()
        
        return story
    
    def _is_thinking_line(self, line: str) -> bool:
        """判断是否是思考过程行"""
        thinking_indicators = [
            "I'm", "I've", "Now I'm", "I am", "I have",
            "**Analyzing", "**Formulating", "**Crafting",
            "**Evaluating", "**Synthesizing", "**Defining",
            "**Designing", "**Planning", "**Refining",
            "**Comprehending", "**Formulating", "**Integrating",
            "我正在", "我已经", "现在", "接下来",
            "Crafting", "Designing", "Formulating", "Planning"
        ]
        
        line_lower = line.lower()
        return any(indicator.lower() in line_lower for indicator in thinking_indicators)
    
    def _looks_like_story_start(self, line: str) -> bool:
        """判断是否看起来像故事开头"""
        # 检查是否主要是中文
        chinese_chars = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
        if chinese_chars < len(line) * 0.5:  # 至少50%是中文
            return False
        
        # 检查长度
        if len(line) < 10:
            return False
        
        # 检查是否包含故事性词汇
        story_keywords = ['照片', '故事', '回忆', '时光', '那年', '那时', '记得', '想起']
        return any(keyword in line for keyword in story_keywords)
    
    def _call_api_for_story(
        self, prompt: str, on_stream_chunk: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        调用API生成故事（支持Gemini和混元；Gemini 支持流式时实时回调）
        
        Args:
            prompt: 故事生成提示词
            on_stream_chunk: 可选，流式时每段文本回调
            
        Returns:
            生成的故事文本
        """
        if config.USE_HUNYUAN:
            result = self._call_hunyuan_text_api(prompt)
            if on_stream_chunk is not None and result:
                on_stream_chunk(result)
            return result
        if config.USE_GEMINI and on_stream_chunk is not None:
            return self._call_gemini_text_api_stream(prompt, on_stream_chunk)
        if config.USE_GEMINI:
            return self._call_gemini_text_api(prompt)
        return self._call_hunyuan_text_api(prompt)
    
    def _call_gemini_text_api(self, prompt: str) -> str:
        """调用Gemini API生成文本"""
        import requests
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": config.TEMPERATURE,
                "maxOutputTokens": getattr(config, "STORY_MAX_OUTPUT_TOKENS", 4096)
            }
        }
        
        # Gemini API通常将API Key作为查询参数
        url = f"{self.api_endpoint}?key={self.api_key}"
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            # Gemini响应格式
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if parts and "text" in parts[0]:
                        return parts[0]["text"]
            
            return str(result)
                
        except Exception as e:
            print(f"Gemini API调用错误: {e}")
            if 'response' in locals():
                print(f"响应内容: {response.text}")
            # 失败时返回空，让调用方使用 _generate_story_from_analysis 根据用户回答生成
            return ""

    def _call_gemini_text_api_stream(self, prompt: str, on_chunk: Callable[[str], None]) -> str:
        """调用 Gemini 流式 API，每收到一段文本就调用 on_chunk，最后返回完整文本"""
        import json
        import requests
        
        model_name = getattr(config, "GEMINI_MODEL_NAME", "gemini-2.5-pro")
        base = (self.api_endpoint or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        # 如果 base 已经包含 /models/xxx，就直接在后面拼 :streamGenerateContent
        if "/models/" in base:
            url = f"{base}:streamGenerateContent?key={self.api_key}"
        else:
            url = f"{base}/models/{model_name}:streamGenerateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": config.TEMPERATURE,
                "maxOutputTokens": getattr(config, "STORY_MAX_OUTPUT_TOKENS", 4096),
            },
        }
        full_text = []
        try:
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    s = line.strip()
                    if s.startswith("data:"):
                        s = s[5:].strip()
                    if not s or s == "[DONE]":
                        continue
                    try:
                        data = json.loads(s)
                        if "candidates" in data and data["candidates"]:
                            c = data["candidates"][0]
                            if "content" in c and "parts" in c["content"] and c["content"]["parts"]:
                                # Gemini 2.5 可能返回多个 part：带 thought:true 的是思考过程，只收集非 thought 的正文
                                for part in c["content"]["parts"]:
                                    if part.get("thought") is True:
                                        continue
                                    text = part.get("text", "")
                                    if text:
                                        full_text.append(text)
                                        on_chunk(text)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass
        except Exception as e:
            print(f"Gemini 流式 API 错误: {e}")
        # 失败时返回空，让调用方使用 _generate_story_from_analysis 根据用户回答生成
        return "".join(full_text) if full_text else ""
    
    def _call_hunyuan_text_api(self, prompt: str) -> str:
        """调用混元API生成文本（原始实现）"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        model = getattr(config, "HUNYUAN_TEXT_MODEL", "hunyuan-vision")
        max_tokens = getattr(config, "STORY_MAX_OUTPUT_TOKENS", 4096)
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config.TEMPERATURE,
            "max_tokens": max_tokens,
        }
        try:
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=90,
            )
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return self._get_mock_story()
                
        except Exception as e:
            print(f"混元API调用错误: {e}")
            # 失败时返回空，让调用方使用 _generate_story_from_analysis 根据用户回答生成
            return ""
    
    def _get_mock_story(self) -> str:
        """返回模拟故事（用于测试）"""
        return """这是一张珍贵的家庭合影，记录着那个年代的温馨时光。

照片中，一对中年夫妇和一个年轻女孩站在一栋老式建筑前，他们的笑容自然纯真。背景里的砖瓦平房，是那个时代典型的建筑风格，见证了无数家庭的日常生活。

从照片中可以看出，这是80年代的一个普通家庭。男士穿着中山装，显得庄重而朴实；女士的花衬衫则带着那个年代的时尚印记；年轻女孩的眼中闪烁着对未来的憧憬。

这张照片不仅仅是一张简单的合影，它承载着一个家庭的记忆，记录着那个时代的生活风貌。每一处细节，每一个表情，都在诉说着那个年代的故事。

时光荏苒，照片中的人或许已经老去，但这份记忆却永远定格在那一刻，成为家族传承的珍贵财富。"""
