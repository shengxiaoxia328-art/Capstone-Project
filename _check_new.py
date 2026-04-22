import json
for m in ['claude_opus46','gpt54']:
    d = json.load(open(f'simulation/evaluation/{m}/{m}_results.json', encoding='utf-8'))
    total = d["total_samples"]
    ok = d["successful_samples"]
    final = d["final"]["mean"]
    print(f"{m}: total={total} ok={ok} final={final}")
    for s in d['samples']:
        sid = s['sample_id']
        fs = s.get('final_score', 0)
        err = 'ERR' if 'error' in s else 'OK'
        print(f"  {sid}: {fs:.2f} {err}")
