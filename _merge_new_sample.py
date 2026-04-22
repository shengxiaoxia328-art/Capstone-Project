"""将新样本(升排长__照相馆)合并回各模型的 results.json，标记为真实数据"""
import json, statistics

NEW_SAMPLE_SCORES = {
    "mimo": {"sample_id": "升排长__照相馆", "photo_score": 4.0, "story_score": 4.5, "interview_score": 1.03, "final_score": 3.66, "data_type": "real"},
    "kimi": {"sample_id": "升排长__照相馆", "photo_score": 3.67, "story_score": 4.67, "interview_score": 0.74, "final_score": 3.58, "data_type": "real"},
    "qwen": {"sample_id": "升排长__照相馆", "photo_score": 3.67, "story_score": 4.5, "interview_score": 2.03, "final_score": 3.76, "data_type": "real"},
    "grok": {"sample_id": "升排长__照相馆", "photo_score": 4.0, "story_score": 4.5, "interview_score": 1.78, "final_score": 3.81, "data_type": "real"},
}

for m in ["mimo", "kimi", "qwen", "grok"]:
    path = f"simulation/evaluation/{m}/{m}_results.json"
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    # 标记旧样本为仿真数据
    for s in d["samples"]:
        if "data_type" not in s:
            s["data_type"] = "simulated"

    # 去重后追加新样本
    d["samples"] = [s for s in d["samples"] if s["sample_id"] != "升排长__照相馆"]
    d["samples"].append(NEW_SAMPLE_SCORES[m])

    # 重新计算统计
    all_s = d["samples"]
    ok = [s for s in all_s if "error" not in s]
    d["total_samples"] = len(all_s)
    d["successful_samples"] = len(ok)
    d["failed_samples"] = len(all_s) - len(ok)

    for key, field in [("photo", "photo_score"), ("story", "story_score"),
                       ("interview", "interview_score"), ("final", "final_score")]:
        vals = [s[field] for s in ok if s.get(field, 0) > 0]
        d[key] = {
            "mean": round(statistics.mean(vals), 2) if vals else 0,
            "std": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0,
            "min": round(min(vals), 2) if vals else 0,
            "max": round(max(vals), 2) if vals else 0,
        }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print(f"{m}: {d['successful_samples']}/{d['total_samples']}  "
          f"photo={d['photo']['mean']:.2f}  story={d['story']['mean']:.2f}  "
          f"interview={d['interview']['mean']:.2f}  final={d['final']['mean']:.2f}")

print("\nDone - all models merged with 11 samples")
