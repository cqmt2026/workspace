#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话沉淀脚本 - obsidian_session_archive.py

功能：将当日Cron产出、分析内容沉淀到Obsidian知识库
触发：每天22:00自动运行（配合晚间日志审计）
用法：
  python obsidian_session_archive.py                    # 默认模式：沉淀今日内容
  python obsidian_session_archive.py --list-sources      # 列出可沉淀的来源
"""

import os
import sys
import datetime
import json
import glob
import io

# ========== 配置 ==========
OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"
WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"
INVESTMENT = os.path.join(WORKSPACE, "workspace-investment")
DOUYIN_DOWNLOADS = os.path.join(WORKSPACE, "douyin-downloads")

AREA_MAP = {
    "小说": ("01-小说", "小说"),
    "自媒体": ("01-小说", "自媒体"),
    "投资": ("03-知识", "投资"),
    "数学": ("01-小说", "数学动画"),
    "系统": ("03-项目", "贾维斯系统"),
    "技术": ("03-投资", "技术"),
    "热点": ("01-小说", "自媒体/热点素材"),
    "会话": ("00-日记", "会话记录"),
}


def save_session_note(title, content, category="会话"):
    """保存会话内容到Obsidian"""
    area, topic = AREA_MAP.get(category, ("00-日记", "会话记录"))
    topic_dir = os.path.join(OBSIDIAN_VAULT, area, topic)
    os.makedirs(topic_dir, exist_ok=True)

    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[:60]
    now = datetime.datetime.now()
    filename = now.strftime("%Y-%m-%d_%H%M") + "_" + safe_title + ".md"
    filepath = os.path.join(topic_dir, filename)

    md = "---\n"
    md += "created: " + now.isoformat() + "\n"
    md += "source: session_archive\n"
    md += "tags: [tag/session_archive]\n"
    md += "area: " + area + "\n"
    md += "topic: " + topic + "\n"
    md += "---\n\n"
    md += "# " + title + "\n\n"
    md += content + "\n\n"
    md += "---\n"
    md += "_by  keyue session_archive | " + now.strftime("%Y-%m-%d %H:%M") + "_\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    return filepath


def scan_douyin_analysis():
    """扫描抖音下载目录中的分析文本"""
    notes = []
    txt_files = glob.glob(os.path.join(DOUYIN_DOWNLOADS, "*_transcript.txt"))
    txt_files += glob.glob(os.path.join(DOUYIN_DOWNLOADS, "*_analysis*.txt"))
    txt_files += glob.glob(os.path.join(DOUYIN_DOWNLOADS, "*_fixed.txt"))

    for fp in txt_files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > 100:
                basename = os.path.basename(fp).replace(".txt", "")
                notes.append({
                    "title": "douyin_analysis_" + basename,
                    "content": content[:3000],
                    "category": "热点"
                })
        except:
            continue

    return notes


def archive_today():
    """执行今日沉淀"""
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    saved_files = []

    # 1. 扫描抖音分析
    douyin_notes = scan_douyin_analysis()
    for note in douyin_notes:
        fp = save_session_note(note["title"], note["content"], note["category"])
        saved_files.append(fp)

    # 2. 汇总
    print("=" * 50)
    print("session archive - " + today_str)
    print("saved " + str(len(saved_files)) + " files")
    for fp in saved_files:
        print("  " + fp)
    print("=" * 50)

    return saved_files


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if "--list-sources" in sys.argv:
        print("Sources:")
        for name, path in [("douyin", DOUYIN_DOWNLOADS)]:
            exists = os.path.exists(path)
            print("  " + ("Y" if exists else "N") + " " + name + ": " + path)
        sys.exit(0)

    archive_today()
