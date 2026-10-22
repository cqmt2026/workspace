#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理临时文件和空目录"""

import os
import shutil

base = r'C:\Users\Administrator\.openclaw\workspace'
total_cleaned = 0

# 1. 清理临时文件和缓存
temp_dirs = [
    os.path.join(base, 'memory', 'temp'),
    os.path.join(base, 'memory', '__pycache__'),
    os.path.join(base, 'scripts', '__pycache__'),
]

for td in temp_dirs:
    if os.path.exists(td):
        try:
            size = 0
            for root, dirs, files in os.walk(td):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.isfile(fp):
                        size += os.path.getsize(fp)
            shutil.rmtree(td)
            total_cleaned += size
            print(f'Cleaned: {td.replace(base + chr(92), "")} - {size/1024/1024:.1f}MB')
        except Exception as e:
            print(f'Failed to clean {td}: {e}')

# 2. 清理空目录
empty_removed = 0
for root, dirs, files in os.walk(base):
    if any(x in root for x in ['.git', 'node_modules', 'agency-agents']):
        continue
    if not files and not dirs:
        try:
            os.rmdir(root)
            empty_removed += 1
            print(f'Removed empty dir: {root.replace(base + chr(92), "")}')
        except Exception as e:
            print(f'Failed to remove {root}: {e}')

# 3. 子系统大小
print('\n=== Subsystem sizes ===')
subsystems = [
    'workspace-investment',
    'workspace-maphot', 
    'workspace-pv',
    'workspace-social',
    'workspace-math',
    'workspace-baiduagent',
]

for d in subsystems:
    dp = os.path.join(base, d)
    if os.path.exists(dp):
        size = 0
        for root, dirs, files in os.walk(dp):
            for f in files:
                fp = os.path.join(root, f)
                if os.path.isfile(fp):
                    size += os.path.getsize(fp)
        print(f'{d}: {size/1024/1024/1024:.2f}GB')

# 4. 其他大目录
print('\n=== Other large directories ===')
other_dirs = ['embeddings', 'lancedb', 'logs', 'media', 'output', 'outputs']
for d in other_dirs:
    dp = os.path.join(base, d)
    if os.path.exists(dp):
        size = 0
        for root, dirs, files in os.walk(dp):
            for f in files:
                fp = os.path.join(root, f)
                if os.path.isfile(fp):
                    size += os.path.getsize(fp)
        print(f'{d}: {size/1024/1024:.1f}MB')

print(f'\n=== Summary ===')
print(f'Temp cleaned: {total_cleaned/1024/1024:.1f}MB')
print(f'Empty dirs removed: {empty_removed}')
