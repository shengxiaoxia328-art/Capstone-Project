"""
结果汇总和可视化脚本
汇总多个模型的评测结果，生成对比表和图表
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import csv

PROJECT_ROOT = Path(__file__).parent.parent.parent
EVALUATION_DIR = PROJECT_ROOT / "simulation" / "evaluation"


class ResultsSummarizer:
    """评测结果汇总器"""

    def __init__(self):
        self.evaluation_dir = EVALUATION_DIR
        self.evaluation_dir.mkdir(parents=True, exist_ok=True)

    def collect_results(self) -> Dict[str, Dict[str, Any]]:
        """收集所有模型的评测结果"""
        results = {}
        
        for model_dir in self.evaluation_dir.iterdir():
            if not model_dir.is_dir():
                continue
            
            results_file = model_dir / f"{model_dir.name}_results.json"
            if results_file.exists():
                with open(results_file, "r", encoding="utf-8") as f:
                    results[model_dir.name] = json.load(f)
        
        return results

    def generate_summary_table(self, results: Dict[str, Dict[str, Any]]) -> str:
        """生成汇总表 (CSV 格式)"""
        if not results:
            return "没有找到任何评测结果"

        table_file = self.evaluation_dir / "summary_table.csv"
        
        with open(table_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # 表头
            writer.writerow([
                "模型",
                "样本数",
                "成功数",
                "失败数",
                "照片分(平均)",
                "照片分(标准差)",
                "故事分(平均)",
                "故事分(标准差)",
                "访谈分(平均)",
                "访谈分(标准差)",
                "最终分(平均)",
                "最终分(标准差)",
            ])
            
            # 数据行
            for model_name, result in sorted(results.items()):
                writer.writerow([
                    model_name,
                    result.get("total_samples", 0),
                    result.get("successful_samples", 0),
                    result.get("failed_samples", 0),
                    result["photo"]["mean"],
                    result["photo"]["std"],
                    result["story"]["mean"],
                    result["story"]["std"],
                    result["interview"]["mean"],
                    result["interview"]["std"],
                    result["final"]["mean"],
                    result["final"]["std"],
                ])
        
        print(f"✓ 汇总表已生成: {table_file}")
        return str(table_file)

    def print_comparison_table(self, results: Dict[str, Dict[str, Any]]):
        """打印对比表（终端）"""
        if not results:
            print("没有找到任何评测结果")
            return

        print("\n" + "="*120)
        print("多模型评测结果对比表".center(120))
        print("="*120)
        
        header = [
            "模型",
            "样本数",
            "成功",
            "失败",
            "照片分↓",
            "照片σ",
            "故事分↓",
            "故事σ",
            "访谈分↓",
            "访谈σ",
            "最终分↓",
            "最终σ",
        ]
        print(f"{header[0]:<20}"
              f"{header[1]:>6} {header[2]:>5} {header[3]:>5} "
              f"{header[4]:>8} {header[5]:>6} "
              f"{header[6]:>8} {header[7]:>6} "
              f"{header[8]:>8} {header[9]:>6} "
              f"{header[10]:>8} {header[11]:>6}")
        print("-"*120)
        
        for model_name, result in sorted(results.items()):
            print(f"{model_name:<20}"
                  f"{result.get('total_samples', 0):>6} "
                  f"{result.get('successful_samples', 0):>5} "
                  f"{result.get('failed_samples', 0):>5} "
                  f"{result['photo']['mean']:>8.2f} {result['photo']['std']:>6.2f} "
                  f"{result['story']['mean']:>8.2f} {result['story']['std']:>6.2f} "
                  f"{result['interview']['mean']:>8.2f} {result['interview']['std']:>6.2f} "
                  f"{result['final']['mean']:>8.2f} {result['final']['std']:>6.2f}")
        
        print("="*120 + "\n")

    def generate_visualization(self, results: Dict[str, Dict[str, Any]]):
        """生成可视化图表（需要 matplotlib）"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            print("⚠ matplotlib 未安装，跳过可视化生成")
            print("  可通过以下命令安装: pip install matplotlib")
            return

        if not results:
            print("没有数据可用于可视化")
            return

        models = list(sorted(results.keys()))
        
        # 准备数据
        metrics = {
            "photo": [results[m]["photo"]["mean"] for m in models],
            "story": [results[m]["story"]["mean"] for m in models],
            "interview": [results[m]["interview"]["mean"] for m in models],
            "final": [results[m]["final"]["mean"] for m in models],
        }
        
        metric_labels = {
            "photo": "照片分",
            "story": "故事分",
            "interview": "访谈分",
            "final": "最终分",
        }

        # 1. 柱状图：最终分对比
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("多模型评测结果对比", fontsize=16, fontweight="bold")

        # 最终分
        ax = axes[0, 0]
        colors = plt.cm.Set3(np.linspace(0, 1, len(models)))
        ax.bar(models, metrics["final"], color=colors, alpha=0.8)
        ax.set_ylabel("分数", fontsize=11)
        ax.set_title("最终综合分", fontsize=12, fontweight="bold")
        ax.set_ylim([0, 5])
        ax.grid(axis="y", alpha=0.3)
        for i, v in enumerate(metrics["final"]):
            ax.text(i, v + 0.1, f"{v:.2f}", ha="center", va="bottom", fontsize=10)

        # 照片分
        ax = axes[0, 1]
        ax.bar(models, metrics["photo"], color=colors, alpha=0.8)
        ax.set_ylabel("分数", fontsize=11)
        ax.set_title("照片理解分", fontsize=12, fontweight="bold")
        ax.set_ylim([0, 5])
        ax.grid(axis="y", alpha=0.3)
        for i, v in enumerate(metrics["photo"]):
            ax.text(i, v + 0.1, f"{v:.2f}", ha="center", va="bottom", fontsize=10)

        # 故事分
        ax = axes[1, 0]
        ax.bar(models, metrics["story"], color=colors, alpha=0.8)
        ax.set_ylabel("分数", fontsize=11)
        ax.set_title("故事生成分", fontsize=12, fontweight="bold")
        ax.set_ylim([0, 5])
        ax.grid(axis="y", alpha=0.3)
        for i, v in enumerate(metrics["story"]):
            ax.text(i, v + 0.1, f"{v:.2f}", ha="center", va="bottom", fontsize=10)

        # 访谈分
        ax = axes[1, 1]
        ax.bar(models, metrics["interview"], color=colors, alpha=0.8)
        ax.set_ylabel("分数", fontsize=11)
        ax.set_title("访谈质量分", fontsize=12, fontweight="bold")
        ax.set_ylim([0, 5])
        ax.grid(axis="y", alpha=0.3)
        for i, v in enumerate(metrics["interview"]):
            ax.text(i, v + 0.1, f"{v:.2f}", ha="center", va="bottom", fontsize=10)

        plt.tight_layout()
        
        # 保存图表
        plot_file = self.evaluation_dir / "benchmark_comparison.png"
        plt.savefig(plot_file, dpi=150, bbox_inches="tight")
        print(f"✓ 对比图表已生成: {plot_file}")

        # 2. 雷达图：多维度对比
        fig, axes = plt.subplots(1, len(models), figsize=(4*len(models), 4), subplot_kw=dict(projection="polar"))
        if len(models) == 1:
            axes = [axes]

        categories = ["照片分", "故事分", "访谈分"]
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]

        for idx, model in enumerate(models):
            ax = axes[idx]
            values = [
                results[model]["photo"]["mean"],
                results[model]["story"]["mean"],
                results[model]["interview"]["mean"],
            ]
            values += values[:1]
            
            ax.plot(angles, values, "o-", linewidth=2, label=model, color=colors[idx])
            ax.fill(angles, values, alpha=0.25, color=colors[idx])
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, fontsize=10)
            ax.set_ylim([0, 5])
            ax.set_title(model, fontsize=12, fontweight="bold", pad=20)
            ax.grid(True)

        plt.tight_layout()
        radar_file = self.evaluation_dir / "radar_comparison.png"
        plt.savefig(radar_file, dpi=150, bbox_inches="tight")
        print(f"✓ 雷达图已生成: {radar_file}")

        plt.close("all")


def main():
    summarizer = ResultsSummarizer()
    results = summarizer.collect_results()
    
    if not results:
        print("⚠ 未找到任何评测结果")
        print("  请先运行: python simulation/scripts/eval_single_model.py --model <model_name>")
        return

    print(f"\n发现 {len(results)} 个模型的评测结果")
    
    summarizer.print_comparison_table(results)
    summarizer.generate_summary_table(results)
    summarizer.generate_visualization(results)
    
    print("✓ 所有总结已生成完毕")


if __name__ == "__main__":
    main()
