"""
真实数据 vs 模拟数据 置信区间对比分析
"""
import json, os, math
from collections import defaultdict

BASE = "D:/desktop/Tencent Capstone Project/simulation/evaluation"
MODELS = ["mimo", "kimi", "qwen", "grok", "gpt54"]
METRICS = ["photo_score", "story_score", "interview_score", "final_score"]
METRIC_NAMES = {"photo_score": "照片理解", "story_score": "故事生成", 
                "interview_score": "访谈质量", "final_score": "综合评分"}

def load_results(model, tag=""):
    suffix = f"_{tag}" if tag else ""
    path = f"{BASE}/{model}{suffix}/{model}_results.json"
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 只取成功的样本
    ok = [s for s in data["samples"] if not ("error" in s and s.get("photo_score", 0) == 0)]
    return ok

def mean_std(values):
    n = len(values)
    if n == 0:
        return 0, 0, 0
    mu = sum(values) / n
    if n < 2:
        return mu, 0, n
    var = sum((x - mu) ** 2 for x in values) / (n - 1)
    return mu, math.sqrt(var), n

def ci_95(mu, std, n):
    """95% CI using t-distribution approximation (t ~ 2.0 for n~10)"""
    if n < 2:
        return mu, mu
    # t critical values for 95% CI
    t_vals = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571,
              7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 11: 2.201,
              12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131}
    t = t_vals.get(n, 1.96)
    margin = t * std / math.sqrt(n)
    return mu - margin, mu + margin

def welch_t_test(mu1, s1, n1, mu2, s2, n2):
    """Welch's t-test for unequal variances"""
    if n1 < 2 or n2 < 2 or (s1 == 0 and s2 == 0):
        return 0, 1.0  # no data
    se = math.sqrt(s1**2/n1 + s2**2/n2)
    if se == 0:
        return 0, 1.0
    t_stat = (mu1 - mu2) / se
    # Welch-Satterthwaite degrees of freedom
    num = (s1**2/n1 + s2**2/n2)**2
    den = (s1**2/n1)**2/(n1-1) + (s2**2/n2)**2/(n2-1)
    df = num / den if den > 0 else 1
    # Approximate p-value using normal distribution (good for df > 5)
    # For small df, this is conservative
    p_approx = 2 * (1 - _norm_cdf(abs(t_stat)))
    return t_stat, p_approx

def _norm_cdf(x):
    """Standard normal CDF approximation"""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def cohen_d(mu1, s1, n1, mu2, s2, n2):
    """Effect size (Cohen's d)"""
    sp = math.sqrt(((n1-1)*s1**2 + (n2-1)*s2**2) / (n1+n2-2)) if (n1+n2-2) > 0 else 1
    return (mu1 - mu2) / sp if sp > 0 else 0

# ==================== 主分析 ====================
print("=" * 80)
print("   真实数据 vs 模拟数据 — 置信区间对比分析报告")
print("=" * 80)

# 1. 各模型各指标详细对比
all_real_finals = []
all_sim_finals = []

for model in MODELS:
    sim = load_results(model)
    real = load_results(model, "real")
    if not sim or not real:
        print(f"\n[跳过] {model}: 数据不完整")
        continue
    
    print(f"\n{'─' * 70}")
    print(f"  模型: {model.upper()}")
    print(f"  模拟样本数: {len(sim)}  |  真实样本数: {len(real)}")
    print(f"{'─' * 70}")
    print(f"  {'指标':<10} {'模拟均值':>8} {'模拟CI':>16} {'真实均值':>8} {'真实CI':>16} {'差异':>6} {'p值':>8} {'显著?':>5}")
    print(f"  {'-'*10} {'-'*8} {'-'*16} {'-'*8} {'-'*16} {'-'*6} {'-'*8} {'-'*5}")
    
    for metric in METRICS:
        sim_vals = [s.get(metric, 0) for s in sim]
        real_vals = [s.get(metric, 0) for s in real]
        
        mu_s, std_s, n_s = mean_std(sim_vals)
        mu_r, std_r, n_r = mean_std(real_vals)
        
        ci_s = ci_95(mu_s, std_s, n_s)
        ci_r = ci_95(mu_r, std_r, n_r)
        
        t_stat, p_val = welch_t_test(mu_r, std_r, n_r, mu_s, std_s, n_s)
        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
        diff = mu_r - mu_s
        
        name = METRIC_NAMES[metric]
        ci_s_str = f"[{ci_s[0]:.2f},{ci_s[1]:.2f}]"
        ci_r_str = f"[{ci_r[0]:.2f},{ci_r[1]:.2f}]"
        print(f"  {name:<10} {mu_s:>8.2f} {ci_s_str:>16} {mu_r:>8.2f} {ci_r_str:>16} {diff:>+6.2f} {p_val:>8.4f} {sig:>5}")
        
        if metric == "final_score":
            all_sim_finals.extend(sim_vals)
            all_real_finals.extend(real_vals)

# 2. 综合排名对比
print(f"\n{'=' * 80}")
print("   综合排名对比")
print(f"{'=' * 80}")

sim_ranking = []
real_ranking = []
for model in MODELS:
    sim = load_results(model)
    real = load_results(model, "real")
    if sim:
        vals = [s.get("final_score", 0) for s in sim]
        mu, std, n = mean_std(vals)
        ci = ci_95(mu, std, n)
        sim_ranking.append((model, mu, std, n, ci))
    if real:
        vals = [s.get("final_score", 0) for s in real]
        mu, std, n = mean_std(vals)
        ci = ci_95(mu, std, n)
        real_ranking.append((model, mu, std, n, ci))

sim_ranking.sort(key=lambda x: -x[1])
real_ranking.sort(key=lambda x: -x[1])

print(f"\n  {'排名':>4} {'模拟数据':^30} {'|':^3} {'真实数据':^30}")
print(f"  {'-'*4} {'-'*30} {'|':^3} {'-'*30}")
for i in range(max(len(sim_ranking), len(real_ranking))):
    sim_str = ""
    real_str = ""
    if i < len(sim_ranking):
        m, mu, std, n, ci = sim_ranking[i]
        sim_str = f"{m:<8} {mu:.2f} [{ci[0]:.2f},{ci[1]:.2f}]"
    if i < len(real_ranking):
        m, mu, std, n, ci = real_ranking[i]
        real_str = f"{m:<8} {mu:.2f} [{ci[0]:.2f},{ci[1]:.2f}]"
    print(f"  {i+1:>4} {sim_str:<30} {'|':^3} {real_str:<30}")

# 3. 全局统计
print(f"\n{'=' * 80}")
print("   全局统计 (所有模型 final_score 汇总)")
print(f"{'=' * 80}")
mu_s_all, std_s_all, n_s_all = mean_std(all_sim_finals)
mu_r_all, std_r_all, n_r_all = mean_std(all_real_finals)
ci_s_all = ci_95(mu_s_all, std_s_all, n_s_all)
ci_r_all = ci_95(mu_r_all, std_r_all, n_r_all)
t_all, p_all = welch_t_test(mu_r_all, std_r_all, n_r_all, mu_s_all, std_s_all, n_s_all)
d_all = cohen_d(mu_r_all, std_r_all, n_r_all, mu_s_all, std_s_all, n_s_all)

print(f"  模拟数据: n={n_s_all}, mean={mu_s_all:.3f}, std={std_s_all:.3f}, 95%CI=[{ci_s_all[0]:.3f}, {ci_s_all[1]:.3f}]")
print(f"  真实数据: n={n_r_all}, mean={mu_r_all:.3f}, std={std_r_all:.3f}, 95%CI=[{ci_r_all[0]:.3f}, {ci_r_all[1]:.3f}]")
print(f"  差异: {mu_r_all - mu_s_all:+.3f}")
print(f"  Welch t = {t_all:.3f}, p = {p_all:.4f}")
print(f"  Cohen's d = {d_all:.3f} ({'可忽略' if abs(d_all)<0.2 else '小' if abs(d_all)<0.5 else '中等' if abs(d_all)<0.8 else '大'}效应)")

ci_overlap = not (ci_r_all[1] < ci_s_all[0] or ci_s_all[1] < ci_r_all[0])
print(f"  置信区间{'重叠' if ci_overlap else '不重叠'} → {'无显著差异' if ci_overlap else '存在显著差异'}")

print(f"\n{'=' * 80}")
print("   结论")
print(f"{'=' * 80}")
if p_all >= 0.05:
    print("  ✓ 真实数据与模拟数据之间无统计学显著差异 (p ≥ 0.05)")
    print("  ✓ 模拟基准数据具有较好的代表性，可作为模型评估的有效参考")
else:
    print("  ✗ 真实数据与模拟数据之间存在统计学显著差异 (p < 0.05)")
    print(f"  效应量 Cohen's d = {d_all:.3f}，实际差异{'较小' if abs(d_all)<0.5 else '值得关注'}")

# 4. 各模型配对分析
print(f"\n{'=' * 80}")
print("   各模型 真实-模拟 配对检验 (final_score)")
print(f"{'=' * 80}")
print(f"  {'模型':<8} {'模拟':>6} {'真实':>6} {'差异':>7} {'t值':>7} {'p值':>8} {'效应量':>7} {'结论':>8}")
print(f"  {'-'*8} {'-'*6} {'-'*6} {'-'*7} {'-'*7} {'-'*8} {'-'*7} {'-'*8}")

for model in MODELS:
    sim = load_results(model)
    real = load_results(model, "real")
    if not sim or not real:
        continue
    sim_vals = [s.get("final_score", 0) for s in sim]
    real_vals = [s.get("final_score", 0) for s in real]
    mu_s, std_s, n_s = mean_std(sim_vals)
    mu_r, std_r, n_r = mean_std(real_vals)
    t_stat, p_val = welch_t_test(mu_r, std_r, n_r, mu_s, std_s, n_s)
    d = cohen_d(mu_r, std_r, n_r, mu_s, std_s, n_s)
    sig = "显著*" if p_val < 0.05 else "不显著"
    print(f"  {model:<8} {mu_s:>6.2f} {mu_r:>6.2f} {mu_r-mu_s:>+7.2f} {t_stat:>7.2f} {p_val:>8.4f} {d:>+7.2f} {sig:>8}")

print()
