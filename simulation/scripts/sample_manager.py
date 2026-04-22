"""
样本库生成助手
从 markdown 访谈稿提取文段，快速扩展 test_samples.json
"""

import json
from pathlib import Path
import re


def extract_memoir_sections(markdown_file):
    """从 markdown 文件提取回忆录段落"""
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按标题或段落分割
    sections = re.split(r'\n## |\n### |\n#### ', content)
    
    result = []
    for section in sections:
        if len(section.strip()) > 100:  # 过滤太短的段落
            result.append(section.strip())
    
    return result


def create_sample_template(sample_id, image_path, image_desc, memoir_text):
    """创建样本模板"""
    return {
        "sample_id": sample_id,
        "image_path": image_path,
        "image_description": image_desc,
        "memoir_text": memoir_text,
        "mme_tasks": [
            {
                "question": "[根据图片补充具体问题]",
                "answer": "[yes/no]"
            }
        ],
        "mmbench_tasks": [
            {
                "question": "[根据图片补充具体问题]",
                "options": {
                    "A": "[选项]",
                    "B": "[选项]",
                    "C": "[选项]",
                    "D": "[选项]"
                },
                "answer": "[A/B/C/D]"
            }
        ],
        "hooks": [
            "[时间]",
            "[地点]",
            "[关键人物]",
            "[其他元素]"
        ],
        "reference_story": "[根据图片和访谈稿生成的参考故事段落]"
    }


def quick_add_samples():
    """交互式快速添加样本"""
    config_file = Path(__file__).parent / "test_samples.json"
    
    with open(config_file, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    
    print("=" * 60)
    print("样本库快速扩展工具")
    print("=" * 60)
    print(f"\n当前样本数: {len(samples)}")
    
    while True:
        print("\n选项:")
        print("1. 添加新样本")
        print("2. 从markdown提取段落")
        print("3. 查看现有样本")
        print("4. 导出为Excel（用于手动编辑）")
        print("5. 退出")
        
        choice = input("\n选择 [1-5]: ").strip()
        
        if choice == "1":
            print("\n--- 添加新样本 ---")
            sample_id = f"sample_{len(samples) + 1:03d}"
            image_path = input("图片路径 (相对于项目根): ").strip()
            image_desc = input("图片描述: ").strip()
            memoir_text = input("回忆录文段 (可多行，输入END结束):\n")
            
            lines = []
            while memoir_text.lower() != "end":
                lines.append(memoir_text)
                memoir_text = input()
            memoir_text = "\n".join(lines)
            
            template = create_sample_template(sample_id, image_path, image_desc, memoir_text)
            samples.append(template)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(samples, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 样本 {sample_id} 已添加 (需手动补充 MME/MMBench/hooks/story)")
        
        elif choice == "2":
            print("\n--- 从markdown提取 ---")
            md_files = [
                "回忆录成文与访谈稿_知青篇.md",
                "回忆录成文与访谈稿_乡村教师篇.md",
                "回忆录成文与访谈稿_个体户篇.md"
            ]
            
            for idx, md_file in enumerate(md_files, 1):
                print(f"{idx}. {md_file}")
            
            file_choice = input("选择 [1-3]: ").strip()
            if file_choice in ["1", "2", "3"]:
                md_path = Path(".") / md_files[int(file_choice) - 1]
                if md_path.exists():
                    sections = extract_memoir_sections(md_path)
                    print(f"\n找到 {len(sections)} 个段落")
                    for i, section in enumerate(sections[:5], 1):
                        print(f"\n{i}. {section[:100]}...")
                else:
                    print(f"文件不存在: {md_path}")
        
        elif choice == "3":
            print(f"\n现有 {len(samples)} 个样本:")
            for sample in samples:
                print(f"  - {sample['sample_id']}: {sample['memoir_text'][:50]}...")
        
        elif choice == "4":
            print("\n提示: 导出功能可通过以下步骤完成:")
            print("1. python -c \"import json; samples = json.load(open('simulation/config/test_samples.json')); import csv; ...")
            print("   或直接用 JSON viewer 打开 test_samples.json")
        
        elif choice == "5":
            print("\n退出")
            break
        
        else:
            print("无效选择")


if __name__ == "__main__":
    quick_add_samples()
