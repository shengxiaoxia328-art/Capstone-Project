"""生成 Benchmark 对比图表"""
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ── 读取数据 ──────────────────────────────────────────────
models_cfg = {
    'gpt54':        {'full': 'OpenAI GPT-5.4',          'file': 'simulation/evaluation/gpt54/gpt54_results.json'},
    'qwen':         {'full': 'Alibaba Qwen3.5-122B',    'file': 'simulation/evaluation/qwen/qwen_results.json'},
    'mimo':         {'full': 'Xiaomi MiMo-v2-Omni',     'file': 'simulation/evaluation/mimo/mimo_results.json'},
    'claude_opus46':{'full': 'Anthropic Claude Opus 4.6','file': 'simulation/evaluation/claude_opus46/claude_opus46_results.json'},
    'kimi':         {'full': 'Moonshot Kimi-K2.5',      'file': 'simulation/evaluation/kimi/kimi_results.json'},
    'grok':         {'full': 'xAI Grok-4.20-Beta',      'file': 'simulation/evaluation/grok/grok_results.json'},
}

data = {}
for k, v in models_cfg.items():
    with open(v['file'], 'r', encoding='utf-8') as f:
        d = json.load(f)
    data[k] = {
        'name': v['full'],
        'photo': d['photo']['mean'],
        'story': d['story']['mean'],
        'interview': d['interview']['mean'],
        'final': d['final']['mean'],
        'photo_std': d['photo']['std'],
        'story_std': d['story']['std'],
        'interview_std': d['interview']['std'],
        'final_std': d['final']['std'],
        'success': d['successful_samples'],
        'total': d['total_samples'],
    }

# 按 final 降序排列
order = sorted(data.keys(), key=lambda k: -data[k]['final'])
names  = [data[k]['name'] for k in order]
colors = ['#4C72B0', '#55A868', '#C44E52', '#8172B2', '#CCB974', '#64B5CD']

# ── 1) 分项 + 综合 柱状图 ────────────────────────────────
metrics = ['photo', 'story', 'interview', 'final']
labels  = ['Photo (30%)', 'Story (50%)', 'Interview (20%)', 'Final Score']

fig, ax = plt.subplots(figsize=(16, 8))
x = np.arange(len(metrics))
n = len(order)
width = 0.8 / n

for i, k in enumerate(order):
    vals = [data[k][m] for m in metrics]
    stds = [data[k][m + '_std'] for m in metrics]
    bars = ax.bar(x + i * width, vals, width, yerr=stds, capsize=3,
                  label=names[i], color=colors[i % len(colors)], alpha=0.88)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08,
                f'{val:.2f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

ax.set_xticks(x + width * (n - 1) / 2)
ax.set_xticklabels(labels, fontsize=12)
ax.set_ylabel('Score (1-5)', fontsize=12)
ax.set_ylim(0, 5.8)
ax.set_title('Multi-Model Benchmark Comparison — Chinese Elderly Memoir Photo Stories',
             fontsize=14, fontweight='bold', pad=12)
ax.legend(fontsize=10, loc='upper right')
ax.grid(axis='y', alpha=0.3)
fig.tight_layout()
fig.savefig('benchmark_bar_chart.png', dpi=180)
print('Saved benchmark_bar_chart.png')

# ── 2) 雷达图 ────────────────────────────────────────────
radar_metrics = ['photo', 'story', 'interview']
radar_labels  = ['Photo\n(30%)', 'Story\n(50%)', 'Interview\n(20%)']
angles = np.linspace(0, 2 * np.pi, len(radar_metrics), endpoint=False).tolist()
angles += angles[:1]

fig2, ax2 = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
ax2.set_theta_offset(np.pi / 2)
ax2.set_theta_direction(-1)
ax2.set_thetagrids(np.degrees(angles[:-1]), radar_labels, fontsize=12)
ax2.set_ylim(0, 5.2)
ax2.set_yticks([1, 2, 3, 4, 5])

for i, k in enumerate(order):
    vals = [data[k][m] for m in radar_metrics] + [data[k][radar_metrics[0]]]
    ax2.plot(angles, vals, 'o-', linewidth=2, label=names[i], color=colors[i % len(colors)])
    ax2.fill(angles, vals, alpha=0.10, color=colors[i % len(colors)])

ax2.set_title('Dimensional Radar — Photo / Story / Interview',
              fontsize=13, fontweight='bold', y=1.08)
ax2.legend(loc='lower right', bbox_to_anchor=(1.25, 0), fontsize=10)
fig2.tight_layout()
fig2.savefig('benchmark_radar_chart.png', dpi=180)
print('Saved benchmark_radar_chart.png')

# ── 3) 综合排名横向条形图 ──────────────────────────────────
fig3, ax3 = plt.subplots(figsize=(11, 6))
finals = [data[k]['final'] for k in order]
success_rate = [f"{data[k]['success']}/{data[k]['total']}" for k in order]
bars3 = ax3.barh(names, finals, color=[colors[i % len(colors)] for i in range(len(order))], alpha=0.88, height=0.55)
for bar, val, sr in zip(bars3, finals, success_rate):
    ax3.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
             f'{val:.2f}  (success {sr})', va='center', fontsize=11, fontweight='bold')
ax3.set_xlim(0, 5)
ax3.set_xlabel('Final Score (Weighted)', fontsize=12)
ax3.set_title('Overall Ranking — Final Weighted Score', fontsize=14, fontweight='bold')
ax3.invert_yaxis()
ax3.grid(axis='x', alpha=0.3)
fig3.tight_layout()
fig3.savefig('benchmark_ranking_chart.png', dpi=180)
print('Saved benchmark_ranking_chart.png')

# ── 汇总表格打印 ─────────────────────────────────────────
print('\n' + '=' * 90)
print(f"{'Model':<28} {'Photo':>8} {'Story':>8} {'Interview':>10} {'Final':>8} {'Success':>8}")
print('-' * 90)
for k in order:
    d = data[k]
    print(f"{d['name']:<28} {d['photo']:>8.2f} {d['story']:>8.2f} {d['interview']:>10.2f} {d['final']:>8.2f} {d['success']:>3}/{d['total']}")
print('=' * 90)
