"""
检验真实数据是否与仿真数据同分布
方法：基于仿真数据构建 t 分布置信区间，检查真实样本是否落入区间
"""
import json, statistics, math

# scipy 可能不可用，手写 t 分位数 (df=9, 95% two-tailed)
# t_0.025,9 = 2.262
T_CRIT_95 = 2.262  # df=9, alpha=0.05 two-tailed
T_CRIT_90 = 1.833  # df=9, alpha=0.10

REAL_SCORES = {
    "mimo":  {"photo": 4.00, "story": 4.50, "interview": 1.03, "final": 3.66},
    "kimi":  {"photo": 3.67, "story": 4.67, "interview": 0.74, "final": 3.58},
    "qwen":  {"photo": 3.67, "story": 4.50, "interview": 2.03, "final": 3.76},
    "grok":  {"photo": 4.00, "story": 4.50, "interview": 1.78, "final": 3.81},
}

models = ["mimo", "kimi", "qwen", "grok"]
metrics = ["photo", "story", "interview", "final"]
metric_labels = {"photo": "Photo", "story": "Story", "interview": "Interview", "final": "Final"}

print("=" * 100)
print("真实数据 vs 仿真数据 同分布检验 (单样本 t 检验)")
print("H0: 真实样本来自与仿真数据相同的分布")
print("仿真样本 n=10, 真实样本 n=1, 自由度 df=9")
print("=" * 100)

all_results = []

for m in models:
    path = f"simulation/evaluation/{m}/{m}_results.json"
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    # 分离仿真和真实
    sim_samples = [s for s in d["samples"] if s.get("data_type") != "real"]
    
    print(f"\n{'─' * 100}")
    print(f"模型: {m.upper()} (仿真 n={len(sim_samples)})")
    print(f"{'─' * 100}")
    print(f"{'维度':<12} {'仿真均值':>8} {'仿真Std':>8} {'真实值':>8} "
          f"{'95%CI下限':>10} {'95%CI上限':>10} {'t统计量':>8} {'p近似':>8} {'落入95%CI':>10}")
    print(f"{'─' * 100}")

    for met in metrics:
        field = met + "_score"
        sim_vals = [s[field] for s in sim_samples if s.get(field, 0) > 0]
        real_val = REAL_SCORES[m][met]

        n = len(sim_vals)
        mean = statistics.mean(sim_vals)
        std = statistics.stdev(sim_vals) if n > 1 else 0.001

        # 95% CI for population mean (prediction interval for new observation)
        # 预测区间: mean ± t * s * sqrt(1 + 1/n)
        se_pred = std * math.sqrt(1 + 1/n)
        ci95_lo = mean - T_CRIT_95 * se_pred
        ci95_hi = mean + T_CRIT_95 * se_pred

        # t statistic: 真实值偏离仿真均值多少个标准误
        t_stat = (real_val - mean) / se_pred if se_pred > 0 else 0

        # 近似 p 值 (双尾) 用线性插值
        abs_t = abs(t_stat)
        if abs_t < 1.0:
            p_approx = "> 0.30"
            sig = ""
        elif abs_t < T_CRIT_90:
            p_approx = "0.10~0.30"
            sig = ""
        elif abs_t < T_CRIT_95:
            p_approx = "0.05~0.10"
            sig = " *"
        elif abs_t < 3.250:  # t_0.005,9
            p_approx = "< 0.05"
            sig = " **"
        else:
            p_approx = "< 0.01"
            sig = " ***"

        in_ci = "✓ 是" if ci95_lo <= real_val <= ci95_hi else "✗ 否"

        print(f"{metric_labels[met]:<12} {mean:>8.2f} {std:>8.2f} {real_val:>8.2f} "
              f"{ci95_lo:>10.2f} {ci95_hi:>10.2f} {t_stat:>8.2f} {p_approx:>8}{sig} {in_ci:>10}")

        all_results.append({
            "model": m, "metric": met, "sim_mean": mean, "sim_std": std,
            "real_val": real_val, "ci95_lo": ci95_lo, "ci95_hi": ci95_hi,
            "t_stat": t_stat, "in_ci": ci95_lo <= real_val <= ci95_hi
        })

# 汇总
print(f"\n{'=' * 100}")
print("汇总: 真实值落入 95% 预测区间的比例")
print(f"{'=' * 100}")

total = len(all_results)
in_count = sum(1 for r in all_results if r["in_ci"])
print(f"\n总计 {total} 个 (模型×维度) 组合中，{in_count} 个落入 95% 预测区间 ({in_count/total*100:.0f}%)")
print(f"如果真实数据与仿真同分布，期望约 95% 落入区间。")

# 按模型汇总
print(f"\n{'模型':<10} {'落入CI数':>8} {'总数':>6} {'比例':>8}")
for m in models:
    mr = [r for r in all_results if r["model"] == m]
    mc = sum(1 for r in mr if r["in_ci"])
    print(f"{m:<10} {mc:>8} {len(mr):>6} {mc/len(mr)*100:>7.0f}%")

# 按维度汇总
print(f"\n{'维度':<12} {'落入CI数':>8} {'总数':>6} {'比例':>8} {'真实偏移方向'}")
for met in metrics:
    mr = [r for r in all_results if r["metric"] == met]
    mc = sum(1 for r in mr if r["in_ci"])
    avg_diff = statistics.mean([r["real_val"] - r["sim_mean"] for r in mr])
    direction = f"{'↓' if avg_diff < 0 else '↑'} {avg_diff:+.2f}"
    print(f"{metric_labels[met]:<12} {mc:>8} {len(mr):>6} {mc/len(mr)*100:>7.0f}% {direction:>12}")

print(f"\n{'=' * 100}")
print("结论:")
if in_count / total >= 0.85:
    print("  真实数据基本落入仿真数据的95%预测区间，无显著证据表明两者不同分布。")
    print("  但仅1个真实样本，统计力(power)很低，需更多真实数据才能下定论。")
else:
    out_items = [r for r in all_results if not r["in_ci"]]
    print(f"  有 {total - in_count} 个组合超出95%预测区间，存在一定偏移信号。")
    for r in out_items:
        diff = r["real_val"] - r["sim_mean"]
        print(f"    - {r['model'].upper()} {metric_labels[r['metric']]}: "
              f"真实={r['real_val']:.2f} vs 仿真均值={r['sim_mean']:.2f} (偏移 {diff:+.2f})")
    print("  但仅1个真实样本，统计力(power)很低，建议增加真实数据量后重新验证。")
print(f"{'=' * 100}")
