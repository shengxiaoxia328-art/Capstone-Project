import json, os

for m in ['mimo','kimi','qwen','grok']:
    path = f'simulation/evaluation/{m}/{m}_results.json'
    if not os.path.exists(path):
        print(f"{m}: NO FILE")
        continue
    with open(path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    samples = d.get('samples', [])
    ids = [s['sample_id'] for s in samples]
    print(f"{m}: {len(samples)} samples -> {ids}")
