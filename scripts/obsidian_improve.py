# -*- coding: utf-8 -*-
"""
Obsidian知识库 - 今日推荐 & 活跃度监控
每日执行，推荐优质笔记，监控写入活跃度
"""
import os, re, sys, datetime, io
from collections import defaultdict

# 解决Windows终端GBK编码问题
if sys.stdout.encoding and sys.stdout.encoding.upper() in ('GBK', 'CP936'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

VAULT = r'F:\Obsidian\Jarvis'

def main():
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)
    month_ago = today - datetime.timedelta(days=30)

    cats = defaultdict(lambda: {'files': 0, 'today': 0, 'week': 0, 'month': 0})
    all_files = []

    for root, dirs, files in os.walk(VAULT):
        rel = os.path.relpath(root, VAULT)
        if rel.startswith('.'):
            continue
        parts = rel.split(os.sep)
        cat = parts[0] if len(parts) > 1 and parts[0] else '根目录'
        for f in files:
            if not f.endswith('.md'):
                continue
            fp = os.path.join(root, f)
            try:
                mtime_d = datetime.datetime.fromtimestamp(os.path.getmtime(fp)).date()
                cats[cat]['files'] += 1
                if mtime_d == today:
                    cats[cat]['today'] += 1
                if mtime_d >= week_ago:
                    cats[cat]['week'] += 1
                if mtime_d >= month_ago:
                    cats[cat]['month'] += 1
                all_files.append((fp, rel, mtime_d))
            except:
                pass

    total_files = sum(v['files'] for v in cats.values())
    total_today = sum(v['today'] for v in cats.values())
    total_week = sum(v['week'] for v in cats.values())
    total_month = sum(v['month'] for v in cats.values())

    print('=== Obsidian 今日推荐 & 活跃度监控 ===')
    print(f'生成时间: {datetime.datetime.now().isoformat()}')
    print()
    print('--- 活跃度总览 ---')
    print(f'总笔记数: {total_files}')
    print(f'今日修改: {total_today}')
    print(f'本周修改: {total_week}')
    print(f'本月修改: {total_month}')
    print()

    print('--- 各分类活跃度 ---')
    for cat in sorted(cats.keys()):
        v = cats[cat]
        bar = '#' * min(v['today'] + 1, 20)
        print(f'  {cat}: {v["files"]}篇 | 今日+{v["today"]} | 本周+{v["week"]} | 本月+{v["month"]} {bar}')
    print()

    # 今日推荐：本周修改过 + 内容丰富
    recent = []
    for fp, rel, mtime_d in all_files:
        if mtime_d < week_ago:
            continue
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                c = fh.read()
            lines = len(c.split('\n'))
            if lines < 10:
                continue
            title_m = re.search(r'^# (.+)', c, re.MULTILINE)
            title = title_m.group(1).strip() if title_m else os.path.basename(fp).replace('.md', '')
            # 跳过自动生成的索引/模板文件
            if title in ('Dataview索引', '索引', 'README'):
                continue
            recent.append((rel, title, lines, mtime_d, fp))
        except:
            pass

    recent.sort(key=lambda x: x[2], reverse=True)

    print('--- 今日推荐阅读 ---')
    for rel, title, lines, mtime_d, fp in recent[:10]:
        print(f'  - [{title}]({rel}) ({lines}行, {mtime_d})')
    print()

    # 低活跃笔记
    low_active = sum(1 for _, _, m in all_files if m < week_ago)
    print('--- 低活跃笔记 ---')
    print(f'  7天未修改: {low_active}篇')

    stale = sum(1 for _, _, m in all_files if m < month_ago)
    print(f'  30天未修改: {stale}篇')
    print()

    print('✅ 监控完成')


if __name__ == '__main__':
    main()
