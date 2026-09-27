#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可悦 -> Obsidian 快速沉淀
用于处理主人发来的内容，分类写入Obsidian库
用法: python obsidian_save.py "标题" "内容" [分类]

分类可选: 小说 | 自媒体 | 投资 | 数学 | 系统 | 技术 | 热点 | 其他
"""

import os
import sys
import datetime
import re
import io

OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"

AREA_MAP = {
    "小说": ("01-小说", "小说"),
    "自媒体": ("01-小说", "自媒体"),
    "投资": ("03-知识", "投资"),
    "数学": ("01-小说", "数学动画"),
    "系统": ("03-项目", "贾维斯系统"),
    "技术": ("03-投资", "技术"),
    "热点": ("01-小说", "自媒体/热点素材"),
}

def save_note(title, content, category="其他"):
    area, topic = AREA_MAP.get(category, ("03-投资", "其他"))
    topic_dir = os.path.join(OBSIDIAN_VAULT, area, topic)
    os.makedirs(topic_dir, exist_ok=True)

    safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)[:60]
    filename = datetime.date.today().isoformat() + "_" + safe_title + ".md"
    filepath = os.path.join(topic_dir, filename)

    tags = []
    if topic:
        tags.append("tag/" + topic.replace("/", "/tag/"))
    tags.append("tag/" + area.replace("-", ""))
    tag_str = ", ".join(tags)
    now_str = datetime.datetime.now().isoformat()

    md = "---\n"
    md += "created: " + now_str + "\n"
    md += "source: manual_save\n"
    md += "tags: [" + tag_str + "]\n"
    md += "area: " + area + "\n"
    md += "topic: " + topic + "\n"
    md += "---\n\n"
    md += "# " + safe_title + "\n\n"
    md += "> 由 主人 提供\n\n"
    md += content + "\n\n"
    md += "---\n"
    md += "_由 可悦🌸 自动保存_\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    return filepath


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if len(sys.argv) < 3:
        print("用法: python obsidian_save.py <标题> <内容> [分类]")
        print("分类: 小说|自媒体|投资|数学|系统|技术|热点|其他 (默认: 其他)")
        sys.exit(1)

    title = sys.argv[1]
    content = sys.argv[2]
    category = sys.argv[3] if len(sys.argv) > 3 else "其他"

    fp = save_note(title, content, category)
    print("已保存到: " + fp)