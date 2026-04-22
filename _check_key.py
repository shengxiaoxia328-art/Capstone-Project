import requests
KEY = "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"
r = requests.get("https://openrouter.ai/api/v1/auth/key", headers={"Authorization": f"Bearer {KEY}"}, timeout=15)
d = r.json()["data"]
print(f"limit={d['limit']} usage={d['usage']:.2f} remaining={d['limit_remaining']}")

# Quick API test
r2 = requests.post("https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    json={"model": "anthropic/claude-opus-4.6", "messages": [{"role": "user", "content": "say OK"}], "max_tokens": 10},
    timeout=30)
print(f"claude_opus46: {r2.status_code}")

r3 = requests.post("https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    json={"model": "openai/gpt-5.4", "messages": [{"role": "user", "content": "say OK"}], "max_tokens": 20},
    timeout=30)
print(f"gpt54: {r3.status_code}")
