import requests, os

models_to_test = [
    "google/gemini-2.5-flash",
    "google/gemini-2.5-pro",
]

for model in models_to_test:
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say hi in 3 words"}],
                "max_tokens": 20,
            },
            timeout=30,
        )
        data = resp.json()
        if "error" in data:
            print(f"{model}: {resp.status_code} ERROR - {data['error']}")
        elif "choices" in data:
            text = data["choices"][0]["message"]["content"]
            print(f"{model}: {resp.status_code} OK - {text}")
        else:
            print(f"{model}: {resp.status_code} UNKNOWN - {data}")
    except Exception as e:
        print(f"{model}: EXCEPTION - {e}")
