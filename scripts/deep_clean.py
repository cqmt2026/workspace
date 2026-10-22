# -*- coding: utf-8 -*-
"""深度清理脚本"""
import os
import shutil
import psutil

ws = r'C:\Users\Administrator\.openclaw\workspace'

print('=== 清理Git缓存 ===')
paths = [
    os.path.join(ws, 'backup', 'workspace-git'),
    os.path.join(ws, 'workspace-math', '.git'),
]

freed = 0
for p in paths:
    if os.path.exists(p):
        total_size = 0
        for root, dirs, files in os.walk(p):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total_size += os.path.getsize(fp)
                except:
                    pass
        shutil.rmtree(p, ignore_errors=True)
        freed += total_size
        parent = os.path.basename(os.path.dirname(p))
        child = os.path.basename(p)
        print(f'  清理: {parent}/{child} = {total_size/1024**2:.0f}MB')

print(f'总计释放: {freed/1024**2:.0f}MB')

print()
print('=== 清理后磁盘状态 ===')
for d in ['C:', 'D:']:
    disk = psutil.disk_usage(d)
    print(f'{d}: {disk.free/1024**3:.1f}GB ({disk.percent}%)')
