"""
健壮的批量评测脚本 - 自动重跑失败样本直到全部成功
遇到 403 等网络波动会自动等待后重试
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
EVAL_SCRIPT = PROJECT_ROOT / "simulation" / "scripts" / "eval_single_model.py"
EVAL_DIR = PROJECT_ROOT / "simulation" / "evaluation"

MODELS = ["claude_opus46", "gpt54"]
SAMPLES_FILE = "benchmark_data_complete.json"
MAX_ROUNDS = 10         # 最多重跑几轮
WAIT_BETWEEN_RETRY = 90 # 每轮失败后等待秒数

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)

def count_results(model_name):
    """读取结果文件，返回 (成功数, 失败数, 总数)"""
    results_file = EVAL_DIR / model_name / f"{model_name}_results.json"
    if not results_file.exists():
        return 0, 0, 0
    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    ok = data.get("successful_samples", 0)
    fail = data.get("failed_samples", 0)
    total = data.get("total_samples", 0)
    return ok, fail, total

def run_eval(model_name, retry_failed=False):
    """运行一次评测，返回 exit code"""
    cmd = [
        sys.executable, str(EVAL_SCRIPT),
        "--model", model_name,
        "--samples-file", SAMPLES_FILE,
        "--verbose",
    ]
    if retry_failed:
        cmd.append("--retry-failed")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    log(f"  命令: python eval_single_model.py --model {model_name} {'--retry-failed' if retry_failed else ''}")
    
    proc = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=9000,  # 2.5 小时超时
    )
    return proc.returncode

def run_model_with_retries(model_name):
    """对一个模型循环跑直到 11/11 或用完重试次数"""
    log(f"===== 模型 {model_name} =====")
    
    # 第一轮：全量跑
    ok, fail, total = count_results(model_name)
    if ok == 11 and fail == 0:
        log(f"  {model_name} 已有 11/11 成功结果，跳过")
        return True
    
    is_retry = (ok > 0 and fail > 0)
    
    for round_num in range(1, MAX_ROUNDS + 1):
        log(f"  第 {round_num} 轮 ({'retry-failed' if is_retry else '全量'})")
        
        run_eval(model_name, retry_failed=is_retry)
        
        ok, fail, total = count_results(model_name)
        log(f"  结果: {ok}/{total} 成功, {fail} 失败")
        
        if fail == 0 and ok >= 11:
            log(f"  {model_name} 全部成功!")
            return True
        
        if fail > 0 and round_num < MAX_ROUNDS:
            log(f"  还有 {fail} 个失败，等 {WAIT_BETWEEN_RETRY}s 后重试...")
            time.sleep(WAIT_BETWEEN_RETRY)
            is_retry = True
    
    log(f"  {model_name} 在 {MAX_ROUNDS} 轮后仍有失败")
    return False

def print_final_summary(model_name):
    results_file = EVAL_DIR / model_name / f"{model_name}_results.json"
    if not results_file.exists():
        log(f"  {model_name}: 无结果文件")
        return
    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    log(f"  {model_name}: {data['successful_samples']}/{data['total_samples']} 成功")
    log(f"    Photo={data['photo']['mean']:.2f}  Story={data['story']['mean']:.2f}  Interview={data['interview']['mean']:.2f}  Final={data['final']['mean']:.2f}")

def main():
    log("=" * 50)
    log("健壮批量评测 - 开始")
    log("=" * 50)
    
    for model in MODELS:
        run_model_with_retries(model)
    
    log("")
    log("=" * 50)
    log("最终总结")
    log("=" * 50)
    for model in MODELS:
        print_final_summary(model)
    
    log("全部完成!")

if __name__ == "__main__":
    main()
