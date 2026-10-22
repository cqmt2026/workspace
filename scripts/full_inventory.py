#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全系统数据资产盘点 - 完整版"""

import sys
import os
import glob
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\Administrator\.openclaw'

print('='*70)
print('全系统数据资产盘点报告')
print(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
print('='*70)

# ========== 1. 视频资产 ==========
print('\n【一、视频资产】')
video_projects = {}
today = datetime.now().strftime('%Y-%m-%d')
today_count = 0
today_size = 0

for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.mp4'):
            path = os.path.join(root, f)
            rel = os.path.relpath(path, base)
            parts = rel.split(os.sep)
            
            # 分类
            if len(parts) > 1 and parts[0] == 'workspace':
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
            
            try:
                size = os.path.getsize(path)
                video_projects[proj]['count'] += 1
                video_projects[proj]['size'] += size
                
                # 今日统计
                mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d')
                if mtime == today:
                    today_count += 1
                    today_size += size
            except:
                pass

print(f'\n视频总览: {sum(d["count"] for d in video_projects.values())}个')
print(f'今日产出 ({today}): {today_count}个, {today_size/1024/1024:.1f}MB')
print('\n分布详情:')
for proj, data in sorted(video_projects.items(), key=lambda x: -x[1]['count']):
    print(f'  {proj}: {data["count"]}个, {data["size"]/1024/1024:.1f}MB')

# ========== 2. 文档资产 ==========
print('\n【二、文档资产】')
doc_types = [
    ('Markdown文档', '*.md'),
    ('Python脚本', '*.py'),
    ('JSON配置', '*.json'),
    ('日志文件', '*.log'),
    ('环境变量', '.env'),
]

for name, pattern in doc_types:
    files = glob.glob(os.path.join(base, '**', pattern), recursive=True)
    if files:
        total_size = sum(os.path.getsize(f) for f in files if os.path.isfile(f))
        print(f'  {name}: {len(files)}个, {total_size/1024:.0f}KB')

# ========== 3. 子系统目录 ==========
print('\n【三、子系统目录状态】')
subsystems = [
    ('小说系统', 'workspace-novel'),
    ('投资系统', 'workspace-investment'),
    ('自媒体系统', 'workspace-social'),
    ('数学动画', 'workspace-math'),
    ('微信小程序', 'workspace-weixin'),
    ('地图热点', 'workspace-maphot'),
    ('百都系统', 'workspace-baiduagent'),
]

for name, dirname in subsystems:
    path = os.path.join(base, dirname)
    if os.path.isdir(path):
        file_count = sum(len(files) for _, _, files in os.walk(path))
        size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(path) for f in files)
        mp4_count = len(glob.glob(os.path.join(path, '**', '*.mp4'), recursive=True))
        py_count = len(glob.glob(os.path.join(path, '**', '*.py'), recursive=True))
        status = '存在'
        print(f'  {name}: {status} | {file_count}文件, {size/1024/1024:.1f}MB | {py_count}py, {mp4_count}mp4')
    else:
        print(f'  {name}: 不存在')

# ========== 4. 主workspace结构 ==========
print('\n【四、主workspace/ 结构】')
ws_path = os.path.join(base, 'workspace')
if os.path.isdir(ws_path):
    items = sorted([i for i in os.listdir(ws_path) if not i.startswith('.')])
    for item in items[:30]:
        item_path = os.path.join(ws_path, item)
        if os.path.isdir(item_path):
            fc = sum(len(files) for _, _, files in os.walk(item_path))
            sz = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(item_path) for f in files)
            print(f'  DIR: {item}/ | {fc}文件, {sz/1024/1024:.1f}MB')
        else:
            sz = os.path.getsize(item_path) / 1024
            print(f'  FILE: {item} | {sz:.0f}KB')

# ========== 5. 记忆系统 ==========
print('\n【五、记忆系统】')
memory_path = os.path.join(base, 'workspace', 'memory')
if os.path.isdir(memory_path):
    total_files = sum(len(files) for _, _, files in os.walk(memory_path))
    total_size = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(memory_path) for f in files)
    print(f'  memory/ 总计: {total_files}文件, {total_size/1024/1024:.1f}MB')
    
    # 子目录
    for item in sorted(os.listdir(memory_path)):
        item_path = os.path.join(memory_path, item)
        if os.path.isdir(item_path):
            sc = sum(len(files) for _, _, files in os.walk(item_path))
            ss = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(item_path) for f in files)
            if sc > 0:
                print(f'    {item}/: {sc}文件, {ss/1024:.0f}KB')

# ========== 6. 共享知识 ==========
print('\n【六、共享知识】')
shared_path = os.path.join(base, 'workspace', 'shared-knowledge')
if os.path.isdir(shared_path):
    sc = sum(len(files) for _, _, files in os.walk(shared_path))
    ss = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(shared_path) for f in files)
    print(f'  shared-knowledge/: {sc}文件, {ss/1024/1024:.1f}MB')

# ========== 7. 备份 ==========
print('\n【七、备份】')
backup_path = os.path.join(base, 'workspace', 'backup')
if os.path.isdir(backup_path):
    bc = sum(len(files) for _, _, files in os.walk(backup_path))
    bs = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(backup_path) for f in files)
    print(f'  backup/: {bc}文件, {bs/1024/1024:.1f}MB')

# ========== 8. 核心文档 ==========
print('\n【八、核心文档完整性】')
core_docs = ['SOUL.md', 'AGENTS.md', 'USER.md', 'IDENTITY.md', 'TOOLS.md', 'HEARTBEAT.md', 'coding-standards.md', 'MEMORY.md']
for doc in core_docs:
    p = os.path.join(ws_path, doc)
    if os.path.isfile(p):
        sz = os.path.getsize(p) / 1024
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        cn = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        status = 'OK' if cn > 100 else 'WARNING'
        print(f'  [{status}] {doc}: {sz:.0f}KB, {cn}中文字符')
    else:
        print(f'  [MISSING] {doc}')

print('\n' + '='*70)
print('盘点完成')
print('='*70)
