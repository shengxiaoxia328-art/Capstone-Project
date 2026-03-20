#!/usr/bin/env python3
"""
把一段真实回忆录文本加入数据集，用于扩展 simulation/raw/ 下的 memoir。
用法示例：
  # 方式1：从文本文件添加（推荐）
  python add_segment.py --file 我的回忆.txt --memoir memoir_001 --title "某老师回忆录"

  # 方式2：直接传入文本（短文本）
  python add_segment.py --text "1986年春节，我们全家在院子里放鞭炮……" --memoir memoir_001

  # 新建一本回忆录（不写 --memoir 或写不存在的 id）
  python add_segment.py --file 新回忆录.txt --memoir memoir_002 --title "另一本回忆录"
"""
import argparse
import json
import os
import re

# 脚本所在目录为 simulation/scripts/，raw 在 simulation/raw/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIMULATION_DIR = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(SIMULATION_DIR, "raw")


def load_memoir(memoir_id: str):
    path = os.path.join(RAW_DIR, f"{memoir_id}.json")
    if not os.path.exists(path):
        return None, path
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), path


def save_memoir(data: dict, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已写入: {path}")


def next_segment_id(segments: list) -> str:
    """生成下一个 segment_id，如 seg_01, seg_02, seg_03 ..."""
    if not segments:
        return "seg_01"
    ids = []
    for s in segments:
        m = re.match(r"seg_(\d+)", (s.get("segment_id") or "").strip())
        if m:
            ids.append(int(m.group(1)))
    next_num = max(ids, default=0) + 1
    return f"seg_{next_num:02d}"


def add_segment_from_text(
    text: str,
    memoir_id: str,
    title: str = None,
    metadata: dict = None,
):
    text = (text or "").strip()
    if not text:
        print("错误: 文本为空")
        return

    memoir, path = load_memoir(memoir_id)
    if memoir is None:
        memoir = {
            "memoir_id": memoir_id,
            "title": title or f"回忆录_{memoir_id}",
            "segments": [],
        }
    else:
        if title:
            memoir["title"] = title

    new_id = next_segment_id(memoir["segments"])
    segment = {
        "segment_id": new_id,
        "text": text,
        "metadata": metadata or {},
    }
    memoir["segments"].append(segment)
    save_memoir(memoir, path)
    print(f"已添加段落: {new_id}，当前共 {len(memoir['segments'])} 段。")


def main():
    parser = argparse.ArgumentParser(description="将一段真实回忆录加入数据集")
    parser.add_argument("--file", "-f", type=str, help="从该文本文件读取内容（一段或多段，按空行分）")
    parser.add_argument("--text", "-t", type=str, help="直接传入一段文本")
    parser.add_argument("--memoir", "-m", type=str, default="memoir_001", help="回忆录 id，如 memoir_001（不存在则新建）")
    parser.add_argument("--title", type=str, help="回忆录标题（新建或覆盖时使用）")
    parser.add_argument("--theme", type=str, help="本段主题，写入 metadata.theme")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            raw = f.read()
        # 按空行或双换行分成多段，每段非空就加一条
        blocks = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
        if not blocks:
            print("错误: 文件中没有有效段落")
            return
        metadata = {"theme": args.theme} if args.theme else {}
        for i, block in enumerate(blocks):
            seg_meta = {**metadata}
            if len(blocks) > 1:
                seg_meta["block_index"] = i + 1
            add_segment_from_text(block, args.memoir, args.title, seg_meta)
            args.title = None  # 只在第一段时用 title
    elif args.text:
        metadata = {"theme": args.theme} if args.theme else None
        add_segment_from_text(args.text, args.memoir, args.title, metadata)
    else:
        print("请使用 --file 或 --text 提供要添加的文本。")
        parser.print_help()


if __name__ == "__main__":
    main()
