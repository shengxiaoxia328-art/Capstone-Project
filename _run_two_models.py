"""
批量运行 Claude Opus 4.6 和 GPT-5.4 评测，并将进度写入日志文件。
"""
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
LOG_FILE = PROJECT_ROOT / "_eval_progress.log"

MODELS = ["claude_opus46", "gpt54"]

def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def run_model(model_name: str) -> bool:
    log(f"===== 开始评测模型: {model_name} =====")
    
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "simulation" / "scripts" / "eval_single_model.py"),
        "--model", model_name,
        "--samples-file", "benchmark_data_complete.json",
        "--verbose",
    ]
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(PROJECT_ROOT),
            env=env,
        )
        
        for raw_line in iter(proc.stdout.readline, b""):
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            if line:
                log(f"  [{model_name}] {line}")
        
        proc.wait()
        
        if proc.returncode == 0:
            log(f"===== {model_name} 评测完成 (exit=0) =====")
            return True
        else:
            log(f"===== {model_name} 评测失败 (exit={proc.returncode}) =====")
            return False
            
    except Exception as e:
        log(f"===== {model_name} 异常: {e} =====")
        return False

def main():
    # 清空日志
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("")
    
    log("开始批量评测...")
    
    results = {}
    for model in MODELS:
        ok = run_model(model)
        results[model] = "OK" if ok else "FAIL"
    
    log("\n===== 总结 =====")
    for model, status in results.items():
        log(f"  {model}: {status}")
    
    log("全部完成!")

if __name__ == "__main__":
    main()
