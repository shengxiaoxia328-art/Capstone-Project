"""提取新模型每个样本的详细分数用于报告"""
import json

for m in ['claude_opus46', 'gpt54']:
    d = json.load(open(f'simulation/evaluation/{m}/{m}_results.json', encoding='utf-8'))
    print(f"\n=== {m} ===")
    print(f"photo: {d['photo']['mean']}+-{d['photo']['std']}  story: {d['story']['mean']}+-{d['story']['std']}  interview: {d['interview']['mean']}+-{d['interview']['std']}  final: {d['final']['mean']}+-{d['final']['std']}")
    print(f"photo_max: {d['photo']['max']}  story_max: {d['story']['max']}  interview_max: {d['interview']['max']}")
    print(f"photo_min: {d['photo']['min']}  story_min: {d['story']['min']}  interview_min: {d['interview']['min']}")
    
    # real sample
    for s in d['samples']:
        if s['sample_id'] == '升排长__照相馆':
            print(f"\nREAL: photo={s['photo_score']:.2f} story={s['story_score']:.2f} interview={s['interview_score']:.2f} final={s['final_score']:.2f}")
            sim_finals = [x['final_score'] for x in d['samples'] if x['sample_id'] != '升排长__照相馆' and 'error' not in x]
            sim_mean = sum(sim_finals) / len(sim_finals)
            diff = s['final_score'] - sim_mean
            print(f"sim_mean={sim_mean:.2f} diff={diff:+.2f}")
    
    for s in d['samples']:
        p = s.get('photo_score', 0)
        st = s.get('story_score', 0)
        iv = s.get('interview_score', 0)
        f = s.get('final_score', 0)
        dtype = "🔴 真实" if s['sample_id'] == '升排长__照相馆' else "仿真"
        print(f"| {s['sample_id']} | {p:.2f} | {st:.2f} | {iv:.2f} | {f:.2f} | {dtype} |")
