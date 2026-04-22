"""
把新样本(升排长__照相馆)从各模型的 results 中拆出来:
- 单独保存到 simulation/evaluation/single_sample_comparison.json
- 各模型 results 恢复为旧 10 条
- mimo 的旧 10 条已丢失，需另行重跑
"""
import json, copy, statistics

NEW_ID = "升排长__照相馆"
models = ["mimo", "kimi", "qwen", "grok"]

comparison = {"sample_id": NEW_ID, "models": {}}

for m in models:
    path = f"simulation/evaluation/{m}/{m}_results.json"
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    new_sample = None
    old_samples = []
    for s in d["samples"]:
        if s["sample_id"] == NEW_ID:
            new_sample = s
        else:
            old_samples.append(s)

    if new_sample:
        comparison["models"][m] = {
            "photo_score": new_sample.get("photo_score", 0),
            "story_score": new_sample.get("story_score", 0),
            "interview_score": new_sample.get("interview_score", 0),
            "final_score": new_sample.get("final_score", 0),
        }

    # 只有非 mimo 的才恢复（mimo 旧数据已丢）
    if m != "mimo" and len(old_samples) == 10:
        # 重新计算统计
        def calc_stats(key):
            vals = [s[key] for s in old_samples if key in s and s[key] > 0]
            if not vals:
                return {"mean": 0, "std": 0, "min": 0, "max": 0}
            return {
                "mean": round(statistics.mean(vals), 2),
                "std": round(statistics.stdev(vals) if len(vals) > 1 else 0, 2),
                "min": round(min(vals), 2),
                "max": round(max(vals), 2),
            }

        # Preserve all top-level keys except samples and stats
        restored = copy.deepcopy(d)
        restored["samples"] = old_samples
        restored["total_samples"] = 10
        restored["successful_samples"] = sum(1 for s in old_samples if "error" not in s)
        restored["failed_samples"] = sum(1 for s in old_samples if "error" in s and s.get("photo_score", 0) == 0)
        restored["photo"] = calc_stats("photo_score")
        restored["story"] = calc_stats("story_score")
        restored["interview"] = calc_stats("interview_score")
        restored["final"] = calc_stats("final_score")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(restored, f, ensure_ascii=False, indent=2)
        print(f"{m}: restored to {len(old_samples)} samples")
    elif m == "mimo":
        print(f"{m}: skipped (old data lost, needs re-run)")
    else:
        print(f"{m}: unexpected sample count ({len(old_samples)}), skipped")

# 保存 comparison
comp_path = "simulation/evaluation/single_sample_comparison.json"
with open(comp_path, "w", encoding="utf-8") as f:
    json.dump(comparison, f, ensure_ascii=False, indent=2)
print(f"\nSaved comparison: {comp_path}")
print("\n=== 升排长__照相馆 四模型对比 ===")
print(f"{'模型':<8} {'Photo':>6} {'Story':>6} {'Interview':>10} {'Final':>6}")
print("-" * 40)
for m in models:
    if m in comparison["models"]:
        r = comparison["models"][m]
        print(f"{m:<8} {r['photo_score']:>6.2f} {r['story_score']:>6.2f} {r['interview_score']:>10.2f} {r['final_score']:>6.2f}")
