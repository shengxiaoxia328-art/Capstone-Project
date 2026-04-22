import requests

API_KEY = "sk-wTPVmoXWkajGg5qOMOJ5V75pOLm3inHC58oWzpA0236Idu7o"
BASE_URL = "https://4sapi.com/"

models_to_test = [
    "claude-opus-4-6",
    "gemini-2.5-flash-image",
]

# 先试试 /v1/models 看看支持啥
print("=== 测试连通性 ===")
try:
    resp = requests.get(
        f"{BASE_URL}v1/models",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=15,
    )
    print(f"GET /v1/models: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        if "data" in data:
            ids = [m["id"] for m in data["data"]]
            # 只打印 claude 和 gemini 相关的
            relevant = [i for i in ids if "claude" in i.lower() or "gemini" in i.lower()]
            print(f"Claude/Gemini models ({len(relevant)}):")
            for i in sorted(relevant):
                print(f"  {i}")
            if not relevant:
                print(f"Total models: {len(ids)}, first 20:")
                for i in sorted(ids)[:20]:
                    print(f"  {i}")
        else:
            print(f"Response: {str(data)[:500]}")
    else:
        print(f"Response: {resp.text[:500]}")
except Exception as e:
    print(f"Connection error: {e}")

# 测试两个模型 chat completion
print("\n=== 测试模型调用 ===")
for model in models_to_test:
    try:
        resp = requests.post(
            f"{BASE_URL}v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say hi in 3 words"}],
                "max_tokens": 20,
            },
            timeout=60,
        )
        data = resp.json()
        if "error" in data:
            print(f"{model}: {resp.status_code} ERROR - {data['error']}")
        elif "choices" in data:
            text = data["choices"][0]["message"]["content"]
            print(f"{model}: {resp.status_code} OK - {text}")
        else:
            print(f"{model}: {resp.status_code} - {str(data)[:200]}")
    except Exception as e:
        print(f"{model}: EXCEPTION - {e}")
