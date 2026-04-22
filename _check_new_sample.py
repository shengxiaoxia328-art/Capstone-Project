import json

print("=== 新样本 [升排长__照相馆] 各模型得分 ===\n")
for m in ['mimo','kimi','qwen','grok']:
    with open(f'simulation/evaluation/{m}/{m}_results.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    for s in d['samples']:
        if s['sample_id'] == '升排长__照相馆':
            if 'error' in s and s.get('photo_score', 0) == 0:
                print(f"{m}: FAIL")
            else:
                ps = s["photo_score"]
                ss = s["story_score"]
                ivs = s.get("interview_score", 0)
                fs = s["final_score"]
                print(f"{m}: photo={ps:.2f}  story={ss:.2f}  interview={ivs:.2f}  final={fs:.2f}")
            break
    else:
        print(f"{m}: NOT FOUND")
