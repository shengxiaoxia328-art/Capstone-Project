"""
多模型评测框架 - 系统验证脚本
检查所有依赖、配置、文件结构是否就位
"""

import sys
import json
from pathlib import Path
import subprocess


def check_section(title):
    """打印检查区域标题"""
    print(f"\n{'=' * 60}")
    print(f"✓ {title}")
    print('=' * 60)


def run_check(description, check_func):
    """运行单个检查"""
    try:
        if callable(check_func):
            result = check_func()
        else:
            result = check_func
        status = "✓" if result else "✗"
        print(f"{status} {description}")
        return result
    except Exception as e:
        print(f"✗ {description} - {str(e)}")
        return False


def verify_system():
    """完整系统验证"""
    
    # 获取当前工作目录，向上查找 simulation 目录
    project_root = Path.cwd()
    if not (project_root / "simulation").exists():
        project_root = Path(__file__).parent.parent.parent
    
    print(f"\n项目根: {project_root}\n")
    
    passed = 0
    failed = 0
    
    # 1. 检查核心目录
    check_section("1. 目录结构检查")
    
    dirs_to_check = [
        "simulation/config",
        "simulation/scripts",
        "simulation/evaluation",
        "demo/src",
    ]
    
    for dir_path in dirs_to_check:
        full_path = project_root / dir_path
        if run_check(f"目录存在: {dir_path}", lambda p=full_path: p.exists()):
            passed += 1
        else:
            failed += 1
    
    # 2. 检查配置文件
    check_section("2. 配置文件检查")
    
    config_files = [
        "simulation/config/test_samples.json",
        "simulation/config/models.yaml",
        "demo/judge_final.py",
    ]
    
    for file_path in config_files:
        full_path = project_root / file_path
        if run_check(f"配置文件存在: {file_path}", lambda p=full_path: p.exists()):
            passed += 1
        else:
            failed += 1
    
    # 3. 检查样本完整性
    check_section("3. 样本库检查")
    
    def check_samples():
        try:
            with open(project_root / "simulation/config/test_samples.json", encoding='utf-8') as f:
                samples = json.load(f)
            return len(samples) > 0
        except Exception:
            return False
    
    if run_check("样本库非空", check_samples):
        try:
            with open(project_root / "simulation/config/test_samples.json", encoding='utf-8') as f:
                samples = json.load(f)
            print(f"  └─ 当前样本数: {len(samples)}")
            print(f"  └─ 建议至少: 15-20 个样本以获得有效的对比结果")
            if len(samples) >= 10:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  └─ 错误: {e}")
            failed += 1
    else:
        failed += 1
    
    # 4. 检查必需的 Python 模块
    check_section("4. Python 依赖检查")
    
    modules = [
        ("json", "JSON 处理"),
        ("yaml", "YAML 配置"),
        ("matplotlib", "数据可视化"),
        ("numpy", "数值计算"),
        ("subprocess", "进程管理"),
        ("statistics", "统计"),
    ]
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            if run_check(f"{description}: {module_name}", True):
                passed += 1
            else:
                failed += 1
        except ImportError:
            if run_check(f"{description}: {module_name}", False):
                pass
            else:
                print(f"  └─ 安装: pip install {module_name}")
                failed += 1
    
    # 5. 检查脚本导入
    check_section("5. 脚本模块检查")
    
    sys.path.insert(0, str(project_root))
    
    def check_eval_script():
        from simulation.scripts.eval_single_model import SingleModelEvaluator
        return True
    
    def check_aggregate_script():
        from simulation.scripts.aggregate_results import ResultsSummarizer
        return True
    
    if run_check("评测脚本 (eval_single_model.py)", check_eval_script):
        passed += 1
    else:
        failed += 1
    
    if run_check("聚合脚本 (aggregate_results.py)", check_aggregate_script):
        passed += 1
    else:
        failed += 1
    
    # 6. 检查 demo 模块
    check_section("6. Demo 模块检查")
    
    demo_modules = [
        "demo.src.photo_judge",
        "demo.src.story_judge",
        "demo.src.interview_judge",
    ]
    
    for module_name in demo_modules:
        try:
            __import__(module_name)
            if run_check(f"模块可导入: {module_name}", True):
                passed += 1
            else:
                failed += 1
        except ImportError as e:
            if run_check(f"模块可导入: {module_name}", False):
                pass
            else:
                print(f"  └─ 错误: {e}")
                failed += 1
    
    # 7. 检查图片资源
    check_section("7. 图片资源检查")
    
    image_dir = project_root / "image/回忆录访谈稿_三份索引"
    
    def check_images():
        return image_dir.exists() and len(list(image_dir.glob("*.png"))) > 0
    
    if run_check(f"图片目录可用", check_images):
        images = list(image_dir.glob("*.png"))
        print(f"  └─ 找到 {len(images)} 个 PNG 图片")
        passed += 1
    else:
        failed += 1
    
    # 8. 检查 API 密钥配置
    check_section("8. API 密钥配置")
    
    import os
    
    try:
        has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
        if not has_gemini:
            try:
                models_content = (project_root / "simulation/config/models.yaml").read_text(encoding='utf-8')
                has_gemini = "YOUR_" not in models_content or "GEMINI" in models_content
            except:
                pass
    except:
        has_gemini = False
    
    try:
        has_hunyuan = bool(os.environ.get("HUNYUAN_API_KEY"))
        if not has_hunyuan:
            try:
                models_content = (project_root / "simulation/config/models.yaml").read_text(encoding='utf-8')
                has_hunyuan = "YOUR_" not in models_content or "HUNYUAN" in models_content
            except:
                pass
    except:
        has_hunyuan = False
    
    if run_check("Gemini API 密钥配置", has_gemini):
        passed += 1
    else:
        failed += 1
        print("  └─ 需要配置: 设置 GEMINI_API_KEY 环境变量或更新 models.yaml")
    
    if run_check("Hunyuan API 密钥配置", has_hunyuan):
        passed += 1
    else:
        failed += 1
        print("  └─ 需要配置: 设置 HUNYUAN_API_KEY 环境变量或更新 models.yaml")
    
    # 总结
    print(f"\n{'=' * 60}")
    print(f"检查总结")
    print('=' * 60)
    total = passed + failed
    percentage = (passed / total * 100) if total > 0 else 0
    print(f"✓ 通过: {passed}/{total} ({percentage:.0f}%)")
    
    if failed > 0:
        print(f"\n✗ 失败项目: {failed}")
        print("\n建议的后续步骤:")
        print("1. 检查所有缺失的依赖（pip install）")
        print("2. 配置 API 密钥（GEMINI_API_KEY, HUNYUAN_API_KEY）")
        print("3. 扩展样本库至 15+ 个样本 (simulation/config/test_samples.json)")
        print("4. 运行: python simulation/scripts/eval_single_model.py --model gemini --verbose")
    else:
        print("\n✓ 所有项目检查通过！")
        print("\n快速开始:")
        print("1. python simulation/scripts/eval_single_model.py --model gemini")
        print("2. python simulation/scripts/eval_single_model.py --model hunyuan")
        print("3. python simulation/scripts/aggregate_results.py")
    
    return failed == 0


if __name__ == "__main__":
    success = verify_system()
    sys.exit(0 if success else 1)
