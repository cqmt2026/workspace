#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可悦 -> Obsidian 勘误标记
用于标记知识库中内容有误的笔记
用法: python obsidian_correct.py "笔记文件名关键词" "勘误说明"
"""

import os
import sys
import datetime
import re
import io

OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"


def find_note(keyword):
    """根据关键词搜索笔记"""
    matches = []
    for root, dirs, files in os.walk(OBSIDIAN_VAULT):
        if ".obsidian" in root or ".git" in root:
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            if keyword.lower() in f.lower():
                matches.append(os.path.join(root, f))

    return matches


def add_correction(filepath, note):
    """在笔记的frontmatter中添加勘误标记"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    now_str = datetime.datetime.now().isoformat()

    # 检查是否已有frontmatter
    fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        # 检查是否已标记勘误
        if "corrected: true" in fm_text:
            # 追加勘误说明
            new_fm = fm_text + "\ncorrection_note: " + note + "\ncorrected_at: " + now_str
        else:
            new_fm = fm_text + "\ncorrected: true\ncorrection_note: " + note + "\ncorrected_at: " + now_str
        content = content.replace(fm_text, new_fm, 1)
    else:
        # 没有frontmatter，创建
        new_fm = "---\ncorrected: true\ncorrection_note: " + note + "\ncorrected_at: " + now_str + "\n---\n\n"
        content = new_fm + content

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def main():
    if len(sys.argv) < 3:
        print("用法: python obsidian_correct.py <关键词> <勘误说明>")
        print("示例: python obsidian_correct.py \"MLOps\" \"该分析基于过时数据，结论已不适用\"")
        sys.exit(1)

    keyword = sys.argv[1]
    note = sys.argv[2]

    matches = find_note(keyword)
    if not matches:
        print("未找到包含关键词 '" + keyword + "' 的笔记")
        sys.exit(1)

    print("找到 " + str(len(matches)) + " 篇匹配笔记：")
    for i, m in enumerate(matches):
        rel = os.path.relpath(m, OBSIDIAN_VAULT)
        print("  [" + str(i + 1) + "] " + rel)

    if len(matches) == 1:
        fp = add_correction(matches[0], note)
        print("已标记勘误: " + os.path.relpath(fp, OBSIDIAN_VAULT))
    else:
        # 全部标记勘误
        for m in matches:
            fp = add_correction(m, note)
            print("已标记勘误: " + os.path.relpath(fp, OBSIDIAN_VAULT))

    print("勘误标记完成")


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()