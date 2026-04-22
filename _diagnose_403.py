"""诊断 Claude Opus 4.6 via OpenRouter 的 403 问题"""
import requests, os, json

KEY = os.environ.get("OPENROUTER_API_KEY", "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")
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
}

# ===== Test 1: 最简单的文本请求 =====
print("=" * 50)
print("Test 1: 简单文本请求 (claude-opus-4.6)")
payload1 = {
    "model": "anthropic/claude-opus-4.6",
    "messages": [{"role": "user", "content": "say OK"}],
    "max_tokens": 10,
}
try:
    r = requests.post(ENDPOINT, headers=headers, json=payload1, timeout=30)
    print(f"  Status: {r.status_code}")
    print(f"  Headers: {dict(r.headers)}")
    print(f"  Body: {r.text[:500]}")
except Exception as e:
    print(f"  Exception: {e}")

# ===== Test 2: 检查帐户/credits =====
print("\n" + "=" * 50)
print("Test 2: 检查 /auth/key")
try:
    r2 = requests.get("https://openrouter.ai/api/v1/auth/key", headers={"Authorization": f"Bearer {KEY}"}, timeout=15)
    print(f"  Status: {r2.status_code}")
    print(f"  Body: {r2.text[:500]}")
except Exception as e:
    print(f"  Exception: {e}")

# ===== Test 3: 检查 credits =====
print("\n" + "=" * 50)
print("Test 3: 检查 /credits")
try:
    r3 = requests.get("https://openrouter.ai/api/v1/credits", headers={"Authorization": f"Bearer {KEY}"}, timeout=15)
    print(f"  Status: {r3.status_code}")
    print(f"  Body: {r3.text[:500]}")
except Exception as e:
    print(f"  Exception: {e}")

# ===== Test 4: 试一个不需要 VPN 的模型(kimi) =====
print("\n" + "=" * 50)
print("Test 4: kimi (不需要VPN)")
payload4 = {
    "model": "moonshotai/kimi-k2.5",
    "messages": [{"role": "user", "content": "say OK"}],
    "max_tokens": 10,
}
try:
    r4 = requests.post(ENDPOINT, headers=headers, json=payload4, timeout=30)
    print(f"  Status: {r4.status_code}")
    print(f"  Body: {r4.text[:300]}")
except Exception as e:
    print(f"  Exception: {e}")

# ===== Test 5: GPT-5.4 =====
print("\n" + "=" * 50)
print("Test 5: GPT-5.4")
payload5 = {
    "model": "openai/gpt-5.4",
    "messages": [{"role": "user", "content": "say OK"}],
    "max_tokens": 20,
}
try:
    r5 = requests.post(ENDPOINT, headers=headers, json=payload5, timeout=30)
    print(f"  Status: {r5.status_code}")
    print(f"  Body: {r5.text[:300]}")
except Exception as e:
    print(f"  Exception: {e}")
