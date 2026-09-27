#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0 - 读取率监控
在每个知识笔记的 frontmatter 中维护 read_count 和 last_read_at 字段。
提供一个查询函数，按读取频率排序输出。
"""

import os
import re
import datetime
import json
import io
import sys

OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"
TRACK_FILE = os.path.join(OBSIDIAN_VAULT, ".read_tracking.json")


def load_tracking():
    if os.path.exists(TRACK_FILE):
        with open(TRACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_tracking(data):
    os.makedirs(os.path.dirname(TRACK_FILE), exist_ok=True)
    with open(TRACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def scan_and_update_read_counts():
    """扫描所有笔记，如果笔记有 read_count 字段则更新跟踪文件"""
    tracking = load_tracking()
    now = datetime.datetime.now().isoformat()
    today = datetime.date.today().isoformat()

    for root, dirs, files in os.walk(OBSIDIAN_VAULT):
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, OBSIDIAN_VAULT)
            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except:
                continue

            # 读取 frontmatter 中的 read_count
            fm = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
            if fm:
                fm_text = fm.group(1)
                rc_match = re.search(r"read_count:\s*(\d+)", fm_text)
                lr_match = re.search(r"last_read_at:\s*(.+)", fm_text)
                if rc_match:
                    rc = int(rc_match.group(1))
                    lr = lr_match.group(1).strip() if lr_match else ""
                    tracking[rel] = {"read_count": rc, "last_read_at": lr, "updated": today}

    save_tracking(tracking)
    return tracking


def report_unread(days=30):
    """输出超过 days 天未读取的笔记"""
    tracking = load_tracking()
    now = datetime.datetime.now()
    unread = []
    for rel, data in tracking.items():
        lr = data.get("last_read_at", "")
        if lr:
            try:
                dt = datetime.datetime.fromisoformat(lr)
                if (now - dt).days >= days:
                    unread.append((rel, data["read_count"], lr))
            except:
                unread.append((rel, data["read_count"], lr))
    unread.sort(key=lambda x: x[1])
    return unread


def add_read_count_frontmatter():
    """为所有没有 read_count 字段的笔记添加"""
    added = 0
    for root, dirs, files in os.walk(OBSIDIAN_VAULT):
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(root, f)
            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except:
                continue

            # 已经有 read_count 就跳过
            if "read_count:" in content[:500]:
                continue

            # 有 frontmatter 就追加
            fm_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
            if fm_match:
                fm_text = fm_match.group(1)
                new_fm = fm_text.rstrip() + "\nread_count: 0\nlast_read_at: \n"
                new_content = content.replace(fm_text, new_fm, 1)
                with open(fp, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                added += 1
            else:
                # 无 frontmatter，创建一个
                rel = os.path.relpath(fp, OBSIDIAN_VAULT)
                new_content = "---\ncreated: \nsource: \nread_count: 0\nlast_read_at: \n---\n\n" + content
                with open(fp, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                added += 1

    return added


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        n = add_read_count_frontmatter()
        print(f"P0: 为 {n} 篇笔记添加了 read_count frontmatter")
    elif len(sys.argv) > 1 and sys.argv[1] == "--report":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        tracking = scan_and_update_read_counts()
        unread = report_unread(days)
        print(f"P0: 共跟踪 {len(tracking)} 篇笔记")
        print(f"P0: 超过 {days} 天未读取: {len(unread)} 篇")
        for rel, rc, lr in unread[:20]:
            print(f"  {rel} (read_count={rc}, last_read={lr})")
        print(f"P0: 读取频率排名前10:")
        sorted_by_rc = sorted(tracking.items(), key=lambda x: x[1]["read_count"], reverse=True)
        for rel, data in sorted_by_rc[:10]:
            print(f"  {rel}: read_count={data['read_count']}")
    else:
        # 默认：扫描并报告
        tracking = scan_and_update_read_counts()
        print(f"P0: 扫描完成，共跟踪 {len(tracking)} 篇笔记")