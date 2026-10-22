#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理WPS缓存目录"""
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\Administrator\AppData\Roaming\kingsoft'

# 要清理的目录
dirs_to_clean = [
    'personalofflinecache',
    'PDF',
]

total_freed = 0

for d in dirs_to_clean:
    path = os.path.join(base, d)
    if os.path.exists(path):
        try:
            size = sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(path) for f in fn)
            shutil.rmtree(path)
            total_freed += size
            print(f'✅ 已删除: {d} ({size/1024/1024:.1f}MB)')
        except Exception as e:
            print(f'⚠️ 无法删除 {d}: {e}')
    else:
        print(f'⏭️ 不存在: {d}')

# 检查其他可能的大缓存
print('\n检查WPS其他目录:')
for d in os.listdir(base) if os.path.exists(base) else []:
    path = os.path.join(base, d)
    if os.path.isdir(path):
        try:
            size = sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(path) for f in fn)
            if size > 10 * 1024 * 1024:  # >10MB
                print(f'  {d}: {size/1024/1024:.1f}MB')
        except:
            pass

print(f'\n总计释放: {total_freed/1024/1024:.1f}MB')
