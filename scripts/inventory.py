#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全系统数据资产盘点脚本"""

import sys
import os
import glob
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\Administrator\.openclaw'

print('='*60)
print('全系统数据资产盘点报告')
print(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
print('='*60)

# 1. Main workspace
print('\n【主工作区 workspace/】')
ws_path = os.path.join(base, 'workspace')
if os.path.isdir(ws_path):
    categories = {
        'Python脚本': '*.py',
        'Markdown文档': '*.md',
        '视频文件': '*.mp4',
        '图像文件': ['*.jpg', '*.png', '*.jpeg', '*.gif'],
        '配置文件': ['*.json', '*.yaml', '*.yml', '*.env'],
        '日志文件': '*.log',
    }
    
    totals = {}
    for cat, patterns in categories.items():
        if isinstance(patterns, str):
            patterns = [patterns]
        count = 0
        size = 0
        for pat in patterns:
            files = glob.glob(os.path.join(ws_path, '**', pat), recursive=True)
            count += len(files)
            for f in files:
                try:
                    size += os.path.getsize(f)
                except:
                    pass
        if count > 0:
            totals[cat] = (count, size)
    
    for cat, (count, size) in totals.items():
        print(f'  {cat}: {count}个, {size/1024/1024:.1f}MB')
    
    # Top-level dirs
    print('\n  顶级目录:')
    for item in sorted(os.listdir(ws_path)):
        item_path = os.path.join(ws_path, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            file_count = sum(len(files) for _, _, files in os.walk(item_path))
            size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(item_path) for f in files)
            print(f'    {item}/: {file_count}文件, {size/1024/1024:.1f}MB')

# 2. Subsystem workspaces
print('\n【子系统工作区】')
subsystems = [
    ('投资系统', 'workspace-investment'),
    ('百都系统', 'workspace-baiduagent'),
    ('数学动画', 'workspace-math'),
    ('临时目录', 'workspace-tmp'),
]

for name, dirname in subsystems:
    path = os.path.join(base, dirname)
    if os.path.isdir(path):
        file_count = sum(len(files) for _, _, files in os.walk(path))
        size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(path) for f in files)
        mp4_count = len(glob.glob(os.path.join(path, '**', '*.mp4'), recursive=True))
        print(f'  {name}: {file_count}文件, {size/1024/1024:.1f}MB, {mp4_count}视频')
    else:
        print(f'  {name}: 不存在')

# 3. Video assets detailed
print('\n【视频资产详细清单】')
video_projects = {}
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.mp4'):
            path = os.path.join(root, f)
            rel = os.path.relpath(path, base)
            parts = rel.split(os.sep)
            
            if len(parts) > 1:
                if parts[1].startswith('EP'):
                    proj = '数学动画-EP系列'
                elif 'Scene' in parts[1]:
                    proj = f'数学动画-{parts[1]}'
                elif parts[1] == 'media':
                    proj = '数学动画-media'
                elif parts[1] == 'snail-video':
                    proj = '数学动画-snail-video'
                elif parts[1] == 'L4-共享':
                    proj = '共享资源'
                else:
                    proj = f'workspace/{parts[1]}'
            elif 'workspace-maphot' in rel:
                proj = '地图热点'
            elif 'workspace-baiduagent' in rel:
                proj = '百都系统'
            else:
                proj = '其他'
            
            if proj not in video_projects:
                video_projects[proj] = {'count': 0, 'size': 0}
            video_projects[proj]['count'] += 1
            try:
                video_projects[proj]['size'] += os.path.getsize(path)
            except:
                pass

for proj, data in sorted(video_projects.items(), key=lambda x: -x[1]['count']):
    print(f'  {proj}: {data["count"]}个, {data["size"]/1024/1024:.1f}MB')

# 4. Document assets
print('\n【文档资产】')
doc_types = {
    'Markdown': '*.md',
    'Python': '*.py',
    'JSON': '*.json',
    'Log': '*.log',
}
for doc_type, pattern in doc_types.items():
    files = glob.glob(os.path.join(base, '**', pattern), recursive=True)
    if files:
        total_size = sum(os.path.getsize(f) for f in files if os.path.isfile(f))
        print(f'  {doc_type}: {len(files)}个, {total_size/1024:.0f}KB')

# 5. Memory system
print('\n【记忆系统】')
memory_path = os.path.join(base, 'workspace', 'memory')
if os.path.isdir(memory_path):
    file_count = sum(len(files) for _, _, files in os.walk(memory_path))
    size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(memory_path) for f in files)
    print(f'  memory/: {file_count}文件, {size/1024/1024:.1f}MB')
    
    # By subdirectory
    for item in sorted(os.listdir(memory_path)):
        item_path = os.path.join(memory_path, item)
        if os.path.isdir(item_path):
            sub_count = sum(len(files) for _, _, files in os.walk(item_path))
            sub_size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(item_path) for f in files)
            if sub_count > 0:
                print(f'    {item}/: {sub_count}文件, {sub_size/1024:.0f}KB')

# 6. Shared knowledge
print('\n【共享知识】')
shared_path = os.path.join(base, 'workspace', 'shared-knowledge')
if os.path.isdir(shared_path):
    file_count = sum(len(files) for _, _, files in os.walk(shared_path))
    size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(shared_path) for f in files)
    print(f'  shared-knowledge/: {file_count}文件, {size/1024/1024:.1f}MB')

# 7. Backup
print('\n【备份】')
backup_path = os.path.join(base, 'workspace', 'backup')
if os.path.isdir(backup_path):
    file_count = sum(len(files) for _, _, files in os.walk(backup_path))
    size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(backup_path) for f in files)
    print(f'  backup/: {file_count}文件, {size/1024/1024:.1f}MB')

# 8. Today's output
print('\n【今日产出】')
today = datetime.now().strftime('%Y-%m-%d')
today_count = 0
today_size = 0
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.mp4'):
            path = os.path.join(root, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d')
            if mtime == today:
                today_count += 1
                try:
                    today_size += os.path.getsize(path)
                except:
                    pass
print(f'  {today}: {today_count}个视频, {today_size/1024/1024:.1f}MB')

print('\n' + '='*60)
print('盘点完成')
print('='*60)
