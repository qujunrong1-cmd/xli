#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心理学知识引擎 · 知识库统计/检索辅助脚本

用法（在心理学知识引擎 skill 目录下运行）：
  python scripts/kb_stats.py              # 统计知识库概况（目录、文件、卡片数）
  python scripts/kb_stats.py <关键词>      # 在知识库中检索包含关键词的文件与卡片标题
  python scripts/kb_stats.py --stale [N]  # 时效检查：列出采集日期距今 > N 天（默认 180）或状态为「已过时/待核实」的卡片

说明：这是一个轻量只读工具，不修改任何知识文件。
"""
import os
import re
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.join(BASE, "knowledge")


def count_cards(text: str) -> int:
    # 每张卡片以 "## " 二级标题开头（知识卡片标题）
    return len(re.findall(r"^## ", text, flags=re.M))


def walk_md(root: str):
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            # 跳过占位文件与索引文件（不计入知识卡片统计）
            if f.endswith(".md") and not f.startswith(".") and f != "index.md":
                yield os.path.join(dirpath, f)


def stats():
    print("=== 心理学知识库概况 ===\n")
    total_cards = 0
    rows = []
    for path in walk_md(KB):
        rel = os.path.relpath(path, KB)
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        n = count_cards(text)
        total_cards += n
        rows.append((rel, n))
    if not rows:
        print("（知识库为空，尚未录入任何知识卡片）")
        return
    for rel, n in sorted(rows):
        tag = "主题文件" if not rel.startswith("_topics") else "索引"
        print(f"  [{tag}] {rel:<40} 卡片数={n}")
    print(f"\n共 {total_cards} 张知识卡片。")


def search(keyword: str):
    print(f"=== 检索关键词：{keyword} ===\n")
    hits = 0
    for path in walk_md(KB):
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        if keyword.lower() not in text.lower():
            continue
        rel = os.path.relpath(path, KB)
        print(f"● {rel}")
        # 打印命中关键词的卡片标题
        for line in text.splitlines():
            if line.startswith("## ") and keyword.lower() in line.lower():
                print(f"    - {line[3:].strip()}")
        hits += 1
    if hits == 0:
        print("（未找到包含该关键词的内容）")


def stale(threshold_days: int):
    print(f"=== 时效检查（采集日期距今 > {threshold_days} 天，或状态异常）===\n")
    now = datetime.now()
    found = 0
    for path in walk_md(KB):
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        rel = os.path.relpath(path, KB)
        # 按卡片切分
        cards = re.split(r"(?=^## )", text, flags=re.M)
        for card in cards:
            if not card.strip().startswith("## "):
                continue
            title = card.splitlines()[0].replace("## ", "").strip()
            status_m = re.search(r"\*{0,2}状态\*{0,2}[：:]\s*(\S+)", card)
            date_m = re.search(r"\*{0,2}采集日期\*{0,2}[：:]\s*(\d{4}-\d{2}-\d{2})", card)
            status = status_m.group(1) if status_m else "未知"
            date_str = date_m.group(1) if date_m else None
            reasons = []
            if status in ("已过时", "待核实"):
                reasons.append(f"状态={status}")
            if date_str:
                try:
                    d = datetime.strptime(date_str, "%Y-%m-%d")
                    age = (now - d).days
                    if age > threshold_days:
                        reasons.append(f"采集于 {date_str}（{age} 天前）")
                except ValueError:
                    reasons.append("采集日期格式异常")
            else:
                reasons.append("缺采集日期")
            if reasons:
                found += 1
                print(f"● {rel}")
                print(f"    - {title}")
                print(f"    - {'；'.join(reasons)}")
    if found == 0:
        print("（没有需要复查的条目，知识库较新鲜）")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--stale":
        days = 180
        if len(args) > 1 and args[1].isdigit():
            days = int(args[1])
        stale(days)
    elif args:
        search(args[0])
    else:
        stats()
