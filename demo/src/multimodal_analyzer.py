"""
多模态理解模块
使用混元API深度解析照片内容
"""
import base64
import requests
from typing import Dict, List, Optional
from PIL import Image
import io
import config


class MultimodalAnalyzer:
    """多模态照片分析器"""
    
    def __init__(self, api_key: str = None, api_endpoint: str = None):
        """
        初始化分析器
        
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
        
    def _encode_image(self, image_path: str) -> str:
        """
        将图片编码为base64
        
        Args:
            image_path: 图片路径
            
        Returns:
            base64编码的图片字符串
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _encode_image_from_pil(self, image: Image.Image) -> str:
        """
        将PIL Image对象编码为base64
        
        Args:
            image: PIL Image对象
            
        Returns:
            base64编码的图片字符串
        """
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def analyze_image(self, image_path: str = None, image: Image.Image = None) -> Dict:
        """
        分析单张照片，提取视觉细节
        
        Args:
            image_path: 图片文件路径
            image: PIL Image对象（如果提供image_path则忽略此参数）
            
        Returns:
            包含分析结果的字典，包括：
            - visual_elements: 视觉元素（人物、场景、物品等）
            - emotions: 人物表情和情绪
            - clothing: 服饰细节
            - background: 背景建筑和环境
            - era_items: 时代特征物品
            - overall_description: 整体描述
        """
        # 编码图片并获取格式
        image_format = "jpeg"  # 默认格式
        if image_path:
            image_base64 = self._encode_image(image_path)
            # 从文件扩展名判断格式
            if image_path.lower().endswith('.png'):
                image_format = "png"
            elif image_path.lower().endswith('.gif'):
                image_format = "gif"
            elif image_path.lower().endswith('.webp'):
                image_format = "webp"
        elif image:
            image_base64 = self._encode_image_from_pil(image)
            # PIL Image可以获取格式
            if hasattr(image, 'format') and image.format:
                image_format = image.format.lower()
        else:
            raise ValueError("必须提供image_path或image参数")
        
        # 构建分析提示词
        analysis_prompt = """请深度分析这张老照片，提取以下信息：
1. 视觉元素：详细描述照片中的人物（数量、年龄、性别、关系推测）、场景、物品
2. 人物表情和情绪：每个人的表情、姿态、情绪状态
3. 服饰细节：服装样式、颜色、时代特征
4. 背景建筑：建筑风格、年代特征、地理位置推测
5. 时代物品：照片中的物品及其时代特征（如老式电话、旧式家具等）
6. 整体描述：照片的整体氛围、拍摄年代推测、可能的场景

请以结构化的JSON格式返回分析结果。"""
        
        # 调用API（支持Gemini和混元）
        analysis_result = self._call_hunyuan_api(
            image_base64=image_base64,
            prompt=analysis_prompt,
            image_format=image_format
        )
        
        return self._parse_analysis_result(analysis_result)
    
    def _call_hunyuan_api(self, image_base64: str, prompt: str, image_format: str = "jpeg") -> str:
        """
        调用API进行多模态理解（支持Gemini和混元）
        
        Args:
            image_base64: base64编码的图片
            prompt: 分析提示词
            image_format: 图片格式（jpeg, png, gif, webp）
            
        Returns:
            API返回的文本结果
        """
        if config.USE_HUNYUAN:
            return self._call_hunyuan_vision_api(image_base64, prompt, image_format)
        if config.USE_GEMINI:
            return self._call_gemini_vision_api(image_base64, prompt, image_format)
        return self._get_mock_analysis_result()
    
    def _call_gemini_vision_api(self, image_base64: str, prompt: str, image_format: str = "jpeg") -> str:
        """
        调用Gemini API进行多模态理解（使用Gemini原生格式）
        
        Args:
            image_base64: base64编码的图片
            prompt: 分析提示词
            image_format: 图片格式（jpeg, png, gif, webp）
            
        Returns:
            API返回的文本结果
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        # 根据格式设置MIME类型
        mime_types = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp"
        }
        mime_type = mime_types.get(image_format.lower(), "image/jpeg")
        
        # Gemini API使用parts格式（图片+文本）
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": config.TEMPERATURE,
                "maxOutputTokens": 2048
            }
        }
        
        # 使用查询参数格式（已验证可用）
        url = f"{self.api_endpoint}?key={self.api_key}"
        
        try:
            # 图片分析可能需要更长时间，增加超时时间
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120  # 增加到120秒，图片分析需要更长时间
            )
            response.raise_for_status()
            result = response.json()
            
            # Gemini响应格式：candidates[0].content.parts[].text
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    # 提取所有text部分（可能有thought和text）
                    text_parts = []
                    for part in parts:
                        if "text" in part and not part.get("thought", False):
                            text_parts.append(part["text"])
                    if text_parts:
                        return "\n".join(text_parts)
                    # 如果没有非thought的text，使用第一个text
                    for part in parts:
                        if "text" in part:
                            return part["text"]
            
            # 如果格式不同，尝试其他可能的路径
            if "text" in result:
                return result["text"]
            
            return str(result)
                
        except requests.exceptions.Timeout as e:
            print(f"[警告] Gemini API调用超时（120秒）: {e}")
            print("       可能原因：")
            print("       1. 图片文件太大（当前图片约6MB）")
            print("       2. 网络连接较慢")
            print("       3. API服务器响应慢")
            print("       建议：")
            print("       - 尝试压缩图片到5MB以下")
            print("       - 检查网络连接")
            print("       - 稍后重试")
            print("       当前使用模拟数据...")
            return self._get_mock_analysis_result()
        except Exception as e:
            print(f"[警告] Gemini API调用错误: {e}")
            if 'response' in locals():
                print(f"响应内容: {response.text[:200]}")
            print("       当前使用模拟数据...")
            return self._get_mock_analysis_result()
    
    def _call_hunyuan_vision_api(self, image_base64: str, prompt: str, image_format: str = "jpeg") -> str:
        """
        调用混元API进行多模态理解（原始实现）
        
        Args:
            image_base64: base64编码的图片
            prompt: 分析提示词
            
        Returns:
            API返回的文本结果
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "hunyuan-vision",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format if image_format in ('png', 'gif', 'webp') else 'jpeg'};base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
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
                return str(result)
                
        except Exception as e:
            print(f"混元API调用错误: {e}")
            return self._get_mock_analysis_result()
    
    def _parse_analysis_result(self, raw_result: str) -> Dict:
        """
        解析API返回的分析结果
        
        Args:
            raw_result: API返回的原始文本
            
        Returns:
            结构化的分析结果字典
        """
        # 尝试解析JSON，如果失败则使用文本解析
        import json
        try:
            result = json.loads(raw_result)
        except:
            # 如果返回的不是JSON，创建一个结构化结果
            result = {
                "overall_description": raw_result,
                "visual_elements": self._extract_keywords(raw_result, ["人物", "场景", "物品"]),
                "emotions": self._extract_keywords(raw_result, ["表情", "情绪", "笑容"]),
                "clothing": self._extract_keywords(raw_result, ["服装", "服饰", "穿着"]),
                "background": self._extract_keywords(raw_result, ["背景", "建筑", "环境"]),
                "era_items": self._extract_keywords(raw_result, ["物品", "家具", "设备"])
            }
        
        return {
            "visual_elements": result.get("visual_elements", ""),
            "emotions": result.get("emotions", ""),
            "clothing": result.get("clothing", ""),
            "background": result.get("background", ""),
            "era_items": result.get("era_items", ""),
            "overall_description": result.get("overall_description", raw_result)
        }
    
    def _extract_keywords(self, text: str, keywords: List[str]) -> str:
        """从文本中提取包含关键词的句子"""
        sentences = text.split('。')
        relevant = [s for s in sentences if any(kw in s for kw in keywords)]
        return '。'.join(relevant[:3])  # 返回前3个相关句子
    
    def _get_mock_analysis_result(self) -> str:
        """返回模拟分析结果（用于测试）"""
        return """{
            "visual_elements": "照片中有3个人物，看起来是一家人，包括一对中年夫妇和一个年轻女孩。背景是一栋老式建筑。",
            "emotions": "人物表情自然，面带微笑，显得温馨和谐。",
            "clothing": "穿着80年代的服装，男士穿着中山装，女士穿着花衬衫。",
            "background": "背景是一栋砖瓦结构的平房，具有典型的80年代建筑风格。",
            "era_items": "照片中可以看到老式自行车、搪瓷杯等时代特征物品。",
            "overall_description": "这是一张80年代的家庭合影，氛围温馨，展现了那个时代的家庭生活场景。"
        }"""
