import json

models = ['mimo', 'kimi', 'qwen', 'grok']
for m in models:
    with open(f'simulation/evaluation/{m}/{m}_results.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    ok = sum(1 for s in d['samples'] if 'error' not in s)
    fail_count = sum(1 for s in d['samples'] if 'error' in s and s.get('photo_score', 0) == 0)
    print(f'{m}: {ok}/10 success, {fail_count} fail')
    for s in d['samples']:
        sid = s['sample_id']
        if 'error' in s and s.get('photo_score', 0) == 0:
            err_lines = s['error'].strip().split('\n')
            print(f'  FAIL: {sid} -> {err_lines[-1][:80]}')
        else:
            fs = s['final_score']
            print(f'  OK:   {sid} -> final={fs:.2f}')
