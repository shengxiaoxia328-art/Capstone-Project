import json

for m in ['qwen','mimo','kimi','grok']:
    with open(f'simulation/evaluation/{m}/{m}_results.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    pm, ps = d["photo"]["mean"], d["photo"]["std"]
    pmin, pmax = d["photo"]["min"], d["photo"]["max"]
    sm, ss = d["story"]["mean"], d["story"]["std"]
    smin, smax = d["story"]["min"], d["story"]["max"]
    im, is_ = d["interview"]["mean"], d["interview"]["std"]
    imin, imax = d["interview"]["min"], d["interview"]["max"]
    fm, fs = d["final"]["mean"], d["final"]["std"]
    fmin, fmax = d["final"]["min"], d["final"]["max"]
    suc = d["successful_samples"]
    tot = d["total_samples"]
    print(f"=== {m} === {suc}/{tot}")
    print(f"  photo:     {pm:.2f} +/- {ps:.2f}  [{pmin:.2f}, {pmax:.2f}]")
    print(f"  story:     {sm:.2f} +/- {ss:.2f}  [{smin:.2f}, {smax:.2f}]")
    print(f"  interview: {im:.2f} +/- {is_:.2f}  [{imin:.2f}, {imax:.2f}]")
    print(f"  final:     {fm:.2f} +/- {fs:.2f}  [{fmin:.2f}, {fmax:.2f}]")
    for s in d['samples']:
        dt = s.get('data_type', 'simulated')
        tag = ' [REAL]' if dt == 'real' else ''
        print(f"  {s['sample_id']}: photo={s['photo_score']:.2f} story={s['story_score']:.2f} interview={s.get('interview_score',0):.2f} final={s['final_score']:.2f}{tag}")
