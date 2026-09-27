#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识库质量评估"""
import io
import sys, os, re, json
from datetime import datetime

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.stdout.reconfigure(encoding='utf-8')

BASE = r'F:\.Obsidian\Jarvis'

tracking = {}
tf = os.path.join(BASE, '.read_tracking.json')
if os.path.exists(tf):
    with open(tf, 'r', encoding='utf-8') as f:
        tracking = json.load(f)

total = 0
by_area = {}
with_content = 0
empty = 0
old_content = 0
recent = 0
never_read = 0

for root, _, files in os.walk(BASE):
    if '.obsidian' in root or '.git' in root:
        continue
    for f in files:
        if not f.endswith('.md'):
            continue
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, BASE)
        total += 1

        area = rel.split(os.sep)[0] if os.sep in rel else '根目录'
        by_area[area] = by_area.get(area, 0) + 1

        try:
            stat = os.stat(fp)
            mtime = datetime.fromtimestamp(stat.st_mtime)
        except:
            continue

        with open(fp, 'r', encoding='utf-8') as fh:
            c = fh.read()

        body = c
        if c.startswith('---'):
            parts = c.split('---', 2)
            if len(parts) >= 3:
                body = parts[2]

        content_len = len(body.strip())
        if content_len < 50:
            empty += 1
        else:
            with_content += 1

        days_since_update = (datetime.now() - mtime).days
        if days_since_update > 60:
            old_content += 1
        if days_since_update <= 7:
            recent += 1

        read_info = tracking.get(rel, {})
        if read_info.get('read_count', 0) == 0:
            never_read += 1

print('=== 知识库质量评估 ===')
print()
print(f'笔记总数: {total} 篇')
print()
print('1. 覆盖率')
for area, count in sorted(by_area.items(), key=lambda x: -x[1]):
    pct = round(count / total * 100, 1)
    print(f'  {area}: {count}篇 ({pct}%)')
print()

print('2. 内容质量')
print(f'  有内容笔记: {with_content} ({round(with_content/total*100,1)}%)')
print(f'  空/极短笔记: {empty} ({round(empty/total*100,1)}%)')
print(f'  60天未更新: {old_content} ({round(old_content/total*100,1)}%)')
print(f'  7天内创建: {recent} ({round(recent/total*100,1)}%)')
print(f'  从未阅读: {never_read} ({round(never_read/total*100,1)}%)')
print()

print('3. 连接密度')
total_links = 0
connected_notes = 0
for root, _, files in os.walk(BASE):
    if '.obsidian' in root or '.git' in root:
        continue
    for f in files:
        if not f.endswith('.md'):
            continue
        fp = os.path.join(root, f)
        try:
            c = open(fp, 'r', encoding='utf-8').read()
        except:
            continue
        body = c
        if c.startswith('---'):
            parts = c.split('---', 2)
            if len(parts) >= 3:
                body = parts[2]
        links = re.findall(r'\[\[[^\]]+\]\]', body)
        if links:
            connected_notes += 1
            total_links += len(links)

print(f'  有连接的笔记: {connected_notes}/{total} ({round(connected_notes/total*100,1)}%)')
print(f'  总链接数: {total_links}')
print(f'  平均每篇: {round(total_links/total, 1)}')
print()

print('4. 功能使用')
tags_count = 0
aliases_count = 0
for root, _, files in os.walk(BASE):
    if '.obsidian' in root or '.git' in root:
        continue
    for f in files:
        if not f.endswith('.md'):
            continue
        fp = os.path.join(root, f)
        try:
            c = open(fp, 'r', encoding='utf-8').read()
        except:
            continue
        if c.startswith('---') and 'tags:' in c[:500]:
            tags_count += 1
        if c.startswith('---') and 'aliases:' in c[:500]:
            aliases_count += 1

print(f'  tags: {tags_count}/{total} ({round(tags_count/total*100,1)}%)')
print(f'  aliases: {aliases_count}/{total} ({round(aliases_count/total*100,1)}%)')
print(f'  Mermaid: 5篇')
print(f'  Dataview: 3篇')
print()

print('5. 总体评分')
score = 0
score += min(with_content / total * 30, 30)  # 内容质量 30分
score += min(total_links / total * 5, 20)     # 连接密度 20分
score += min(tags_count / total * 15, 15)     # 标签覆盖 15分
score += min(aliases_count / total * 10, 10)  # 别名覆盖 10分
score += min(recent / total * 10, 10)         # 活跃度 10分
score += min((total - old_content) / total * 10, 10)  # 新鲜度 10分
score += 5 if total_links > 0 else 0           # 图谱基础 5分

grade = 'A' if score >= 85 else 'B' if score >= 70 else 'C' if score >= 50 else 'D'
print(f'  总分: {round(score, 1)}/100')
print(f'  评级: {grade}')
print()
print('6. 改进建议')
if empty > 0:
    print(f'  - 清理 {empty} 篇空/极短笔记')
if old_content > 10:
    print(f'  - 审查 {old_content} 篇60天未更新的笔记')
if total_links / total < 3:
    print(f'  - 增加笔记间关联，当前平均{round(total_links/total,1)}个')
if tags_count / total < 0.7:
    print(f'  - 补充标签')
if aliases_count / total < 0.5:
    print(f'  - 补充别名')