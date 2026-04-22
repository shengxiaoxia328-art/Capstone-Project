import json

for m in ['mimo','kimi','qwen','grok']:
    with open(f'simulation/evaluation/{m}/{m}_results.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    pm, ps = d["photo"]["mean"], d["photo"]["std"]
    sm, ss = d["story"]["mean"], d["story"]["std"]
    im, is_ = d["interview"]["mean"], d["interview"]["std"]
    fm, fs = d["final"]["mean"], d["final"]["std"]
    suc = d["successful_samples"]
    tot = d["total_samples"]
    print(f"{m}: photo={pm:.2f}+-{ps:.2f} story={sm:.2f}+-{ss:.2f} interview={im:.2f}+-{is_:.2f} final={fm:.2f}+-{fs:.2f} success={suc}/{tot}")
    for s in d['samples']:
        sid = s['sample_id']
        if 'error' in s and s.get('photo_score', 0) == 0:
            print(f"  FAIL: {sid}")
        else:
            ps_ = s["photo_score"]
            ss_ = s["story_score"]
            is2 = s.get("interview_score", 0)
            fs_ = s["final_score"]
            print(f"  {sid}: photo={ps_:.2f} story={ss_:.2f} interview={is2:.2f} final={fs_:.2f}")
