import json
for model in ['mimo','grok','gpt54']:
    path = f'simulation/evaluation/{model}_real/{model}_results.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    ok = [s for s in data['samples'] if not ('error' in s and s.get('photo_score',0)==0)]
    fail = [s for s in data['samples'] if 'error' in s and s.get('photo_score',0)==0]
    print(f'\n=== {model.upper()} ({len(ok)}/{len(data["samples"])}) ===')
    for s in ok:
        nm = s.get('sample_name', s.get('sample_id', '?'))
        p, st, iv, f = s['photo_score'], s['story_score'], s['interview_score'], s['final_score']
        print("  %-25s P=%.2f S=%.2f I=%.2f F=%.2f" % (nm, p, st, iv, f))
    for s in fail:
        print("  [FAIL] %s" % s.get('sample_name', s.get('sample_id', '?')))
