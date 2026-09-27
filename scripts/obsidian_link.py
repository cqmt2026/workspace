#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可悦 -> Obsidian 知识关联
每周扫描新增笔记，提取关键知识点，生成关联索引
"""

import os
import sys
import datetime
import re
import json
import io

OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"
LINK_FILE = os.path.join(OBSIDIAN_VAULT, "Z-归档", "知识关联图.md")
INDEX_FILE = os.path.join(OBSIDIAN_VAULT, "Z-归档", "知识索引.md")


def extract_keywords(text):
    """提取关键词（简单版本：提取中英文混合关键词）"""
    words = set()
    # 提取中文词组（2-4字）
    cn_pattern = re.findall(r'[\u4e00-\u9fff]{2,8}', text)
    for w in cn_pattern:
        if len(w) >= 2:
            words.add(w)
    # 提取英文术语（大写或含数字的）
    en_pattern = re.findall(r'\b[A-Z][A-Za-z0-9]{2,}\b', text)
    for w in en_pattern:
        words.add(w)
    return list(words)[:20]


def get_new_notes(since_days=7):
    """获取最近N天的新增/修改笔记"""
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=since_days)
    notes = []

    for root, dirs, files in os.walk(OBSIDIAN_VAULT):
        if ".obsidian" in root or ".git" in root:
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            filepath = os.path.join(root, f)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime > cutoff:
                rel_path = os.path.relpath(filepath, OBSIDIAN_VAULT)
                try:
                    with open(filepath, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    notes.append({
                        "path": rel_path,
                        "filepath": filepath,
                        "content": content,
                        "mtime": mtime,
                        "size": len(content),
                    })
                except:
                    pass

    return notes


def find_connections(notes):
    """找笔记之间的关联"""
    connections = []
    keywords_map = {}

    for note in notes:
        title = os.path.splitext(os.path.basename(note["path"]))[0]
        kws = extract_keywords(note["content"])
        keywords_map[note["path"]] = {"title": title, "keywords": kws}

    # 找关键词重叠
    paths = list(keywords_map.keys())
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            a = keywords_map[paths[i]]
            b = keywords_map[paths[j]]
            overlap = set(a["keywords"]) & set(b["keywords"])
            if len(overlap) >= 2:
                connections.append({
                    "from": paths[i],
                    "to": paths[j],
                    "keywords": list(overlap)[:5],
                    "strength": len(overlap),
                })

    # 按关联强度排序
    connections.sort(key=lambda x: -x["strength"])
    return connections, keywords_map


def build_category_index(notes):
    """按分类汇总"""
    cat_index = {}
    for note in notes:
        rel = note["path"]
        parts = rel.replace("\\", "/").split("/")
        if len(parts) >= 2:
            cat = parts[0] + "/" + parts[1]
        else:
            cat = parts[0]
        if cat not in cat_index:
            cat_index[cat] = []
        cat_index[cat].append(note["path"])

    return cat_index


def generate_link_graph(connections, keywords_map, cat_index):
    """生成关联图和索引"""
    today = datetime.date.today().isoformat()
    week_start = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    # 关联图
    md = "# 🕸️ 知识关联图\n\n"
    md += "> 由 可悦🌸 自动生成\n"
    md += "> 周期: " + week_start + " ~ " + today + "\n\n"
    md += "---\n\n"

    if not connections:
        md += "本周未发现新增笔记间的强关联。\n\n"
    else:
        md += "## 🔗 笔记关联\n\n"
        md += "| 关联对 | 共享关键词 | 强度 |\n"
        md += "|--------|-----------|------|\n"
        for c in connections[:20]:
            from_name = keywords_map[c["from"]]["title"]
            to_name = keywords_map[c["to"]]["title"]
            kw_str = ", ".join(c["keywords"])
            md += "| " + from_name + " ↔ " + to_name + " | " + kw_str + " | " + str(c["strength"]) + " |\n"

    md += "\n---\n\n"
    md += "## 🏷️ 本周关键词云\n\n"
    all_kws = {}
    for path, info in keywords_map.items():
        for kw in info["keywords"]:
            all_kws[kw] = all_kws.get(kw, 0) + 1

    top_kws = sorted(all_kws.items(), key=lambda x: -x[1])[:30]
    if top_kws:
        md += "| 关键词 | 出现次数 |\n"
        md += "|--------|---------|\n"
        for kw, count in top_kws:
            md += "| " + kw + " | " + str(count) + " |\n"

    md += "\n---\n"
    md += "_由 可悦🌸 自动维护_"

    # 知识索引
    idx = "# 📋 知识索引\n\n"
    idx += "> 由 可悦🌸 自动生成\n"
    idx += "> 更新: " + today + "\n\n"
    idx += "---\n\n"

    idx += "## 📂 按分类浏览\n\n"
    for cat, note_paths in sorted(cat_index.items()):
        idx += "### " + cat + " (" + str(len(note_paths)) + "篇)\n\n"
        for np in note_paths[:10]:
            idx += "- [[" + np.replace("\\", "/").replace(".md", "") + "]]\n"
        if len(note_paths) > 10:
            idx += "- ...及其他 " + str(len(note_paths) - 10) + " 篇\n"
        idx += "\n"

    idx += "---\n"
    idx += "_由 可悦🌸 自动维护_"

    return md, idx


def main():
    print("可悦知识关联 - " + datetime.datetime.now().isoformat())
    print("Obsidian库: " + OBSIDIAN_VAULT)
    print()

    print("扫描近7天笔记...")
    notes = get_new_notes(7)
    print("  找到 " + str(len(notes)) + " 篇笔记")
    print()

    if not notes:
        print("本周无新笔记，跳过关联生成")
        # 仍然更新索引
        cat_index = build_category_index(get_new_notes(365))
        _, idx = generate_link_graph([], {}, cat_index)
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(idx)
        print("索引已更新: " + INDEX_FILE)
        return

    print("分析关键词...")
    connections, keywords_map = find_connections(notes)
    print("  提取 " + str(len(keywords_map)) + " 篇笔记的关键词")
    print("  发现 " + str(len(connections)) + " 组关联")
    print()

    print("构建分类索引...")
    cat_index = build_category_index(notes)
    print("  覆盖 " + str(len(cat_index)) + " 个分类")
    print()

    print("生成关联图和索引...")
    link_graph, index = generate_link_graph(connections, keywords_map, cat_index)

    os.makedirs(os.path.dirname(LINK_FILE), exist_ok=True)
    with open(LINK_FILE, "w", encoding="utf-8") as f:
        f.write(link_graph)
    print("  关联图: " + LINK_FILE)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(index)
    print("  索引: " + INDEX_FILE)
    print()
    print("可悦知识关联完成")


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()