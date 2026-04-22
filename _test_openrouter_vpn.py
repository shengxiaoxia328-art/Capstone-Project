import requests, os

KEY = os.environ.get("OPENROUTER_API_KEY", "")
URL = "https://openrouter.ai/api/v1/chat/completions"

models = [
    "anthropic/claude-opus-4-6",
    "openai/gpt-5.4",
]

for model in models:
    try:
        resp = requests.post(
            URL,
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": "Say hi"}], "max_tokens": 20},
            timeout=60,
        )
        data = resp.json()
        if "error" in data:
            print(f"{model}: {resp.status_code} ERROR - {data['error']}")
        elif "choices" in data:
            txt = data["choices"][0]["message"]["content"]
            print(f"{model}: {resp.status_code} OK - {txt}")
        else:
            print(f"{model}: {resp.status_code} - {data}")
    except Exception as e:
        print(f"{model}: EXCEPTION - {e}")
