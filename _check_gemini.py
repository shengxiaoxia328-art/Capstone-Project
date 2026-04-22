import requests, os, json

resp = requests.get(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
    timeout=30,
)
models = resp.json().get("data", [])
gemini = [m for m in models if "gemini" in m["id"].lower()]
gemini.sort(key=lambda m: m["id"])

print(f"{'Model ID':<55} {'Context':>8} {'In $/M':>10} {'Out $/M':>10}")
print("-" * 88)
for m in gemini:
    mid = m["id"]
    ctx = m.get("context_length", "?")
    price_in = float(m.get("pricing", {}).get("prompt", 0)) * 1e6
    price_out = float(m.get("pricing", {}).get("completion", 0)) * 1e6
    print(f"{mid:<55} {ctx:>8} {price_in:>10.2f} {price_out:>10.2f}")

print(f"\nTotal Gemini models on OpenRouter: {len(gemini)}")
