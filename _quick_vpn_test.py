import requests, os, sys
key = os.environ.get("OPENROUTER_API_KEY", "")
if not key:
    key = "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"
try:
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": "anthropic/claude-opus-4.6", "messages": [{"role": "user", "content": "say OK"}], "max_tokens": 10},
        timeout=30,
    )
    with open("_vpn_test.txt", "w") as f:
        f.write(f"{r.status_code}\n")
    sys.exit(0)
except Exception as e:
    with open("_vpn_test.txt", "w") as f:
        f.write(f"ERROR: {e}\n")
    sys.exit(1)
