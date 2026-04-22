import json
models = ['mimo','kimi','qwen']
for m in models:
    with open(f'simulation/evaluation/{m}/{m}_results.json','r',encoding='utf-8') as f:
        d = json.load(f)
    for s in d['samples']:
        if 'error' in s and s.get('photo_score',0)==0:
            sid = s['sample_id']
            print(f'=== {m} / {sid} ===')
            err = s['error'].strip()
            lines = err.split('\n')
            for line in lines[-6:]:
                print(line)
            print()
