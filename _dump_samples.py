import json

models = ['mimo','kimi','grok','qwen']

all_data = {}
for m in models:
    with open(f'simulation/evaluation/{m}/{m}_results.json', 'r', encoding='utf-8') as f:
        all_data[m] = json.load(f)

for m in models:
    print(f'MODEL:{m}')
    for s in all_data[m]['samples']:
        sid = s['sample_id']
        if 'error' in s and s.get('photo_score', 0) == 0:
            print(f'  {sid}|FAIL')
        else:
            ps = s['photo_score']
            ss = s['story_score']
            iv = s['interview_score']
            fs = s['final_score']
            print(f'  {sid}|{ps:.2f}|{ss:.2f}|{iv:.2f}|{fs:.2f}')
