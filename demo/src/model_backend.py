"""通用模型后端封装。

支持：
- hunyuan
- gemini
- openai_compatible
- anthropic
"""

import sys
import time
from typing import Any, Dict

import requests

_MAX_RETRIES = 3
_RETRY_BACKOFF = [5, 15, 30]

import config


def get_model_settings(
    api_key: str = None,
    api_endpoint: str = None,
    provider: str = None,
    text_model: str = None,
    vision_model: str = None,
) -> Dict[str, str]:
    if api_key and api_endpoint:
        selected_provider = (provider or config.MODEL_PROVIDER or "custom").lower()
        return {
            "provider": selected_provider,
            "api_key": api_key,
            "api_endpoint": api_endpoint,
            "text_model": text_model or config.MODEL_TEXT_MODEL or config.GEMINI_MODEL_NAME,
            "vision_model": vision_model or config.MODEL_VISION_MODEL or config.GEMINI_MODEL_NAME,
        }

    if config.USE_GENERIC_MODEL:
        return {
            "provider": config.MODEL_PROVIDER,
            "api_key": config.MODEL_API_KEY,
            "api_endpoint": config.MODEL_API_ENDPOINT,
            "text_model": config.MODEL_TEXT_MODEL,
            "vision_model": config.MODEL_VISION_MODEL,
        }

    if config.USE_HUNYUAN:
        return {
            "provider": "hunyuan",
            "api_key": config.HUNYUAN_API_KEY,
            "api_endpoint": config.HUNYUAN_API_ENDPOINT,
            "text_model": config.HUNYUAN_TEXT_MODEL,
            "vision_model": config.HUNYUAN_VISION_MODEL,
        }

    if config.USE_GEMINI:
        return {
            "provider": "gemini",
            "api_key": config.GEMINI_API_KEY,
            "api_endpoint": config.GEMINI_API_ENDPOINT,
            "text_model": config.GEMINI_MODEL_NAME,
            "vision_model": config.GEMINI_MODEL_NAME,
        }

    raise RuntimeError("未检测到可用模型配置，请配置 MODEL_* 或 HUNYUAN_/GEMINI_ 环境变量。")


def get_model_name(settings: Dict[str, str], capability: str) -> str:
    if capability == "vision":
        return settings.get("vision_model") or settings.get("text_model") or "unknown"
    return settings.get("text_model") or settings.get("vision_model") or "unknown"


def call_text_api(
    settings: Dict[str, str],
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    provider = (settings.get("provider") or "").lower()
    if provider == "hunyuan":
        return _call_hunyuan_text(settings, prompt, temperature, max_tokens)
    if provider == "gemini":
        return _call_gemini_text(settings, prompt, temperature, max_tokens, json_mode)
    if provider in {"openai_compatible", "openai", "kimi", "qwen", "deepseek", "minimax"}:
        return _call_openai_compatible_text(settings, prompt, temperature, max_tokens, json_mode)
    if provider == "anthropic":
        return _call_anthropic_text(settings, prompt, temperature, max_tokens)
    raise RuntimeError(f"暂不支持的 provider: {provider}")


def call_vision_api(
    settings: Dict[str, str],
    image_base64: str,
    prompt: str,
    image_format: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> str:
    provider = (settings.get("provider") or "").lower()
    if provider == "hunyuan":
        return _call_hunyuan_vision(settings, image_base64, prompt, image_format, temperature)
    if provider == "gemini":
        return _call_gemini_vision(settings, image_base64, prompt, image_format, temperature, max_tokens)
    if provider in {"openai_compatible", "openai", "kimi", "qwen", "deepseek", "minimax"}:
        return _call_openai_compatible_vision(settings, image_base64, prompt, image_format, temperature, max_tokens)
    if provider == "anthropic":
        return _call_anthropic_vision(settings, image_base64, prompt, image_format, temperature, max_tokens)
    raise RuntimeError(f"暂不支持视觉调用的 provider: {provider}")


def _call_hunyuan_text(settings: Dict[str, str], prompt: str, temperature: float, max_tokens: int) -> str:
    headers = {
        "Authorization": f"Bearer {settings['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": get_model_name(settings, "text"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    response = requests.post(settings["api_endpoint"], headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()
    choices = result.get("choices") or []
    if not choices:
        raise RuntimeError(f"混元文本接口返回格式异常: {result}")
    return choices[0]["message"]["content"]


def _call_hunyuan_vision(
    settings: Dict[str, str],
    image_base64: str,
    prompt: str,
    image_format: str,
    temperature: float,
) -> str:
    headers = {
        "Authorization": f"Bearer {settings['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": get_model_name(settings, "vision"),
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{_mime_type(image_format)};base64,{image_base64}"
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "temperature": temperature,
    }
    response = requests.post(settings["api_endpoint"], headers=headers, json=payload, timeout=90)
    response.raise_for_status()
    result = response.json()
    choices = result.get("choices") or []
    if not choices:
        raise RuntimeError(f"混元视觉接口返回格式异常: {result}")
    return choices[0]["message"]["content"]


def _call_gemini_text(
    settings: Dict[str, str],
    prompt: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    model_name = get_model_name(settings, "text")
    base = settings["api_endpoint"].rstrip("/")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    if "generativelanguage.googleapis.com" in base:
        url = f"{base}/models/{model_name}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": settings["api_key"]}
    else:
        url = _normalize_openai_endpoint(base)
        headers = {"Authorization": f"Bearer {settings['api_key']}", "Content-Type": "application/json"}
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()
    if "choices" in result and result["choices"]:
        return result["choices"][0]["message"]["content"]
    return _extract_gemini_text(result)


def _call_gemini_vision(
    settings: Dict[str, str],
    image_base64: str,
    prompt: str,
    image_format: str,
    temperature: float,
    max_tokens: int,
) -> str:
    model_name = get_model_name(settings, "vision")
    base = settings["api_endpoint"].rstrip("/")
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": _mime_type(image_format), "data": image_base64}},
                ]
            }
        ],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }

    if "generativelanguage.googleapis.com" in base:
        url = f"{base}/models/{model_name}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": settings["api_key"]}
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        return _extract_gemini_text(response.json())

    return _call_openai_compatible_vision(settings, image_base64, prompt, image_format, temperature, max_tokens)


def _call_openai_compatible_text(
    settings: Dict[str, str],
    prompt: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    headers = {
        "Authorization": f"Bearer {settings['api_key']}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": get_model_name(settings, "text"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    endpoint = _normalize_openai_endpoint(settings["api_endpoint"])
    last_err = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=300)
            # 如果 400 且使用了 json_mode，可能模型不支持 response_format，去掉后重试
            if response.status_code == 400 and json_mode and "response_format" in payload:
                print(f"[兼容] 模型不支持 json_mode，去掉 response_format 后重试...", file=sys.stderr)
                payload.pop("response_format", None)
                response = requests.post(endpoint, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            # OpenRouter sometimes returns 200 with error body
            if "error" in result and not result.get("choices"):
                raise RuntimeError(f"API 返回错误: {result['error']}")
            choices = result.get("choices") or []
            if not choices:
                raise RuntimeError(f"OpenAI 兼容文本接口返回格式异常: {result}")
            return choices[0]["message"]["content"]
        except (requests.exceptions.RequestException, RuntimeError) as e:
            last_err = e
            if attempt < _MAX_RETRIES - 1:
                wait = _RETRY_BACKOFF[attempt]
                print(f"[重试] 文本API第{attempt+1}次失败({e}), {wait}s后重试...", file=sys.stderr)
                time.sleep(wait)
    raise RuntimeError(f"文本API {_MAX_RETRIES}次重试均失败: {last_err}")


def _call_openai_compatible_vision(
    settings: Dict[str, str],
    image_base64: str,
    prompt: str,
    image_format: str,
    temperature: float,
    max_tokens: int,
) -> str:
    headers = {
        "Authorization": f"Bearer {settings['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": get_model_name(settings, "vision"),
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{_mime_type(image_format)};base64,{image_base64}"},
                    },
                ],
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    endpoint = _normalize_openai_endpoint(settings["api_endpoint"])
    last_err = None
    for attempt in range(_MAX_RETRIES):
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            if "error" in result and not result.get("choices"):
                raise RuntimeError(f"API 返回错误: {result['error']}")
            choices = result.get("choices") or []
            if not choices:
                raise RuntimeError(f"OpenAI 兼容视觉接口返回格式异常: {result}")
            return choices[0]["message"]["content"]
        except (requests.exceptions.RequestException, RuntimeError) as e:
            last_err = e
            if attempt < _MAX_RETRIES - 1:
                wait = _RETRY_BACKOFF[attempt]
                print(f"[重试] 视觉API第{attempt+1}次失败({e}), {wait}s后重试...", file=sys.stderr)
                time.sleep(wait)
    raise RuntimeError(f"视觉API {_MAX_RETRIES}次重试均失败: {last_err}")


def _call_anthropic_text(
    settings: Dict[str, str],
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    headers = {
        "x-api-key": settings["api_key"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": get_model_name(settings, "text"),
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    }
    response = requests.post(_normalize_anthropic_endpoint(settings["api_endpoint"]), headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()
    return _extract_anthropic_text(result)


def _call_anthropic_vision(
    settings: Dict[str, str],
    image_base64: str,
    prompt: str,
    image_format: str,
    temperature: float,
    max_tokens: int,
) -> str:
    headers = {
        "x-api-key": settings["api_key"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": get_model_name(settings, "vision"),
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": _mime_type(image_format),
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }
    response = requests.post(_normalize_anthropic_endpoint(settings["api_endpoint"]), headers=headers, json=payload, timeout=90)
    response.raise_for_status()
    result = response.json()
    return _extract_anthropic_text(result)


def _normalize_openai_endpoint(endpoint: str) -> str:
    base = (endpoint or "").rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/chat/completions"


def _normalize_anthropic_endpoint(endpoint: str) -> str:
    base = (endpoint or "").rstrip("/")
    if base.endswith("/messages"):
        return base
    if base.endswith("/v1"):
        return f"{base}/messages"
    return f"{base}/messages"


def _extract_gemini_text(result: Dict[str, Any]) -> str:
    candidates = result.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"Gemini 返回格式异常: {result}")
    parts = candidates[0].get("content", {}).get("parts", [])
    texts = [part.get("text", "") for part in parts if part.get("text")]
    if not texts:
        raise RuntimeError(f"Gemini 未返回文本内容: {result}")
    return "\n".join(texts)


def _extract_anthropic_text(result: Dict[str, Any]) -> str:
    contents = result.get("content") or []
    texts = [item.get("text", "") for item in contents if item.get("type") == "text" and item.get("text")]
    if not texts:
        raise RuntimeError(f"Anthropic 返回格式异常: {result}")
    return "\n".join(texts)


def _mime_type(image_format: str) -> str:
    mapping = {
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    return mapping.get((image_format or "jpeg").lower(), "image/jpeg")