"""
故事评分模块
基于 HANNA 六维标准对故事文本进行 LLM 评分
"""
import json
import re
from typing import Dict, List, Optional

import requests

import config


CRITERIA = [
    {
        "key": "relevance",
        "short": "RE",
        "label": "相关性",
        "description": "故事与给定 prompt 或参考文本的匹配程度。若未提供 prompt 或参考文本，则退化为评估故事是否主题集中、不跑题。",
    },
    {
        "key": "coherence",
        "short": "CH",
        "label": "连贯性",
        "description": "故事是否合乎逻辑，叙事是否清晰，时间、因果与人物关系是否说得通。",
    },
    {
        "key": "empathy",
        "short": "EM",
        "label": "共情力",
        "description": "读者能否理解并感受到角色的情绪、处境与情感变化。",
    },
    {
        "key": "surprise",
        "short": "SU",
        "label": "惊喜度",
        "description": "故事发展或结尾是否具有合理的意外性，而非完全平铺直叙。",
    },
    {
        "key": "engagement",
        "short": "EG",
        "label": "吸引力",
        "description": "故事是否能吸引读者继续读下去，是否具有阅读投入感。",
    },
    {
        "key": "complexity",
        "short": "CX",
        "label": "复杂度",
        "description": "故事是否具备足够细节、层次、背景与展开，而非过于单薄。",
    },
]


class StoryJudge:
    """使用现有模型配置对故事进行六维评分。"""

    def __init__(self, api_key: str = None, api_endpoint: str = None):
        if api_key and api_endpoint:
            self.api_key = api_key
            self.api_endpoint = api_endpoint
            self.backend = "custom"
        elif config.USE_HUNYUAN:
            self.api_key = config.HUNYUAN_API_KEY
            self.api_endpoint = config.HUNYUAN_API_ENDPOINT
            self.backend = "hunyuan"
        elif config.USE_GEMINI:
            self.api_key = config.GEMINI_API_KEY
            self.api_endpoint = config.GEMINI_API_ENDPOINT
            self.backend = "gemini"
        else:
            raise RuntimeError("未检测到可用的模型配置，请先在 demo/.env 中配置 Gemini 或混元 API。")

    def judge_story(
        self,
        story: str,
        story_prompt: Optional[str] = None,
        reference_story: Optional[str] = None,
    ) -> Dict:
        """对单篇故事进行评分并返回结构化结果。"""
        story = (story or "").strip()
        if not story:
            raise ValueError("story 不能为空")

        raw_response = self._call_text_api(
            self._build_judge_prompt(
                story=story,
                story_prompt=story_prompt,
                reference_story=reference_story,
            )
        )
        parsed = self._parse_result(raw_response)
        parsed["meta"] = {
            "backend": self.backend,
            "model": self._get_model_name(),
            "has_prompt": bool((story_prompt or "").strip()),
            "has_reference": bool((reference_story or "").strip()),
        }
        return parsed

    def _get_model_name(self) -> str:
        if self.backend == "hunyuan":
            return getattr(config, "HUNYUAN_TEXT_MODEL", "hunyuan-vision")
        return getattr(config, "GEMINI_MODEL_NAME", "gemini-2.5-pro")

    def _build_judge_prompt(
        self,
        story: str,
        story_prompt: Optional[str],
        reference_story: Optional[str],
    ) -> str:
        criteria_text = "\n".join(
            [
                f"- {item['key']} ({item['short']} / {item['label']}): {item['description']}"
                for item in CRITERIA
            ]
        )

        prompt_text = (story_prompt or "").strip() or "未提供"
        reference_text = (reference_story or "").strip() or "未提供"

        return f"""你是一个严格的故事评审员。请基于 HANNA 风格的六维标准，对下面的故事进行 1-5 分评分。

评分标准：
{criteria_text}

要求：
1. 只输出一个 JSON 对象，不要输出 Markdown，不要输出解释性前缀。
2. 每个维度都必须给出整数或一位小数，范围 1 到 5。
3. 解释必须简短具体，并引用故事中的现象，不要写空话。
4. 如果没有提供 prompt 或参考文本，relevance 退化为“主题聚焦度/是否跑题”的判断，但仍按 1-5 分输出。
5. final_score 为六个维度的平均分，保留两位小数。

请严格按照下面的 JSON 结构输出：
{{
  "scores": {{
    "relevance": 0,
    "coherence": 0,
    "empathy": 0,
    "surprise": 0,
    "engagement": 0,
    "complexity": 0
  }},
  "explanations": {{
    "relevance": "",
    "coherence": "",
    "empathy": "",
    "surprise": "",
    "engagement": "",
    "complexity": ""
  }},
  "final_score": 0,
  "summary": ""
}}

Story Prompt:
{prompt_text}

Reference Story:
{reference_text}

Story:
{story}
"""

    def _call_text_api(self, prompt: str) -> str:
        if self.backend == "hunyuan":
            return self._call_hunyuan_text_api(prompt)
        return self._call_gemini_text_api(prompt)

    def _call_gemini_text_api(self, prompt: str) -> str:
        model_name = getattr(config, "GEMINI_MODEL_NAME", "gemini-2.5-pro")
        payload_gemini = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json",
            },
        }
        last_error = None
        base = (self.api_endpoint or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")

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
                    timeout=45,
                )
                response.raise_for_status()
                return self._extract_gemini_text(response.json())
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:300] if e.response.text else str(e)}"
            except Exception as e:
                last_error = str(e)

        headers_bearer = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload_openai = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
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
                response = requests.post(
                    endpoint,
                    headers=headers_bearer,
                    json=payload,
                    timeout=45,
                )
                response.raise_for_status()
                result = response.json()
                if key == "choices" and result.get("choices"):
                    return result["choices"][0]["message"]["content"]
                if key == "candidates" and result.get("candidates"):
                    return self._extract_gemini_text(result)
                if "text" in result:
                    return result["text"]
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text[:300] if e.response.text else str(e)}"
            except Exception as e:
                last_error = str(e)

        raise RuntimeError(f"Gemini 评分请求失败: {last_error or '未知错误'}")

    def _extract_gemini_text(self, result: Dict) -> str:
        candidates = result.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"Gemini 返回格式异常: {result}")
        parts = candidates[0].get("content", {}).get("parts", [])
        texts = [part.get("text", "") for part in parts if part.get("text")]
        if not texts:
            raise RuntimeError(f"Gemini 未返回文本内容: {result}")
        return "\n".join(texts)

    def _call_hunyuan_text_api(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        model = getattr(config, "HUNYUAN_TEXT_MODEL", "hunyuan-vision")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        response = requests.post(
            self.api_endpoint,
            headers=headers,
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        result = response.json()
        choices = result.get("choices") or []
        if not choices:
            raise RuntimeError(f"混元返回格式异常: {result}")
        return choices[0]["message"]["content"]

    def _parse_result(self, raw_response: str) -> Dict:
        data = self._extract_json(raw_response)
        scores = data.get("scores") or {}
        explanations = data.get("explanations") or {}

        normalized_scores = {}
        for item in CRITERIA:
            value = scores.get(item["key"])
            normalized_scores[item["key"]] = self._normalize_score(value, item["key"])

        final_score = data.get("final_score")
        if final_score is None:
            final_score = round(sum(normalized_scores.values()) / len(normalized_scores), 2)
        else:
            final_score = round(float(final_score), 2)

        return {
            "scores": normalized_scores,
            "explanations": {
                item["key"]: str(explanations.get(item["key"], "")).strip()
                for item in CRITERIA
            },
            "final_score": final_score,
            "summary": str(data.get("summary", "")).strip(),
            "raw_response": raw_response,
        }

    def _extract_json(self, text: str) -> Dict:
        text = (text or "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                raise RuntimeError(f"评分结果不是有效 JSON: {text[:500]}")
            return json.loads(match.group(0))

    def _normalize_score(self, value, key: str) -> float:
        if value is None:
            raise RuntimeError(f"评分结果缺少字段: {key}")
        score = round(float(value), 1)
        if score < 1 or score > 5:
            raise RuntimeError(f"评分字段 {key} 超出范围: {score}")
        return score


def format_judgement_for_cli(judgement: Dict) -> str:
    """生成适合 CLI 输出的 JSON 字符串。"""
    ordered_scores = {
        item["key"]: judgement["scores"][item["key"]]
        for item in CRITERIA
    }
    ordered_explanations = {
        item["key"]: judgement["explanations"][item["key"]]
        for item in CRITERIA
    }
    output = {
        "scores": ordered_scores,
        "final_score": judgement["final_score"],
        "summary": judgement["summary"],
        "explanations": ordered_explanations,
        "meta": judgement.get("meta", {}),
    }
    return json.dumps(output, ensure_ascii=False, indent=2)