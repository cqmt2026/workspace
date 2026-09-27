# -*- coding: utf-8 -*-
import os, subprocess
from datetime import datetime

workspace = r'C:\Users\Administrator\.openclaw\workspace'

# 检查各子系统核心脚本是否存在
subsystems = {
    '投资系统': ['workspace-investment/scripts/market_data_collector.py'],
    '小说系统': ['workspace-novel/scripts/novel_workflow.py'],
    '自媒体系统': ['workspace-social/scripts/social_workflow.py'],
    '数学动画': ['workspace-math/scripts/gen_ep1.py'],
    '地图热点': ['workspace-maphot/scripts/core/pipeline.py'],
    '微信小程序': ['workspace-weixin/scripts/'],
}

print('=== 核心脚本检查 ===')
for name, scripts in subsystems.items():
    for s in scripts:
        path = os.path.join(workspace, s)
        exists = os.path.exists(path)
        status = "OK" if exists else "MISSING"
        print(f'{name}: {s} -> {status}')

print()
print('=== 子系统最近活动 ===')
subdirs = {
    '投资系统': 'workspace-investment',
    '小说系统': 'workspace-novel',
    '自媒体系统': 'workspace-social',
    '数学动画': 'workspace-math',
    '地图热点': 'workspace-maphot',
    '微信小程序': 'workspace-weixin',
}

for name, subdir in subdirs.items():
    path = os.path.join(workspace, subdir)
    if not os.path.exists(path):
        print(f'{name}: 目录不存在')
        continue
    newest_time = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(fp)
                if mtime > newest_time:
                    newest_time = mtime
            except:
                pass
    if newest_time > 0:
        days_ago = (datetime.now().timestamp() - newest_time) / 86400
        date_str = datetime.fromtimestamp(newest_time).strftime('%Y-%m-%d %H:%M')
        print(f'{name}: 最后活动 {days_ago:.1f}天前 ({date_str})')
    else:
        print(f'{name}: 无文件')

# 磁盘空间
print()
print('=== 磁盘空间 ===')
for letter in ['C', 'D']:
    try:
        result = subprocess.run(
            ['wmic', 'logicaldisk', f'where DeviceID="{letter}:"', 'get', 'FreeSpace', 'TotalSize'],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 3:
            freespace = int(lines[1].strip()) / (1024**3)
            totalspace = int(lines[2].strip()) / (1024**3)
            used_pct = (1 - freespace / totalspace) * 100 if totalspace > 0 else 0
            print(f'{letter}: 已用 {used_pct:.1f}% (可用 {freespace:.1f}GB / 总计 {totalspace:.1f}GB)')
    except Exception as e:
        print(f'{letter}: 无法获取 - {e}')
