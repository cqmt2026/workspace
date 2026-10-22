#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""深度清理脚本"""

import os
import shutil
import psutil
from datetime import datetime, timedelta

base = r'C:\Users\Administrator\.openclaw\workspace'
cleaned = 0

print("=" * 60)
print("深度清理")
print("=" * 60)

# 1. 清理__pycache__
print("\n[1] 清理__pycache__")
for root, dirs, files in os.walk(base):
    if '__pycache__' in root:
        try:
            size = 0
            for r, d, f in os.walk(root):
                for file in f:
                    fp = os.path.join(r, file)
                    if os.path.isfile(fp):
                        size += os.path.getsize(fp)
            shutil.rmtree(root)
            cleaned += size
            print(f"  Cleaned: {root.replace(base+'\\', '')} ({size/1024:.0f} KB)")
        except Exception as e:
            print(f"  Failed: {root} - {e}")

# 2. 清理临时文件
print("\n[2] 清理临时文件")
temp_dirs = [
    os.path.join(base, 'memory', 'temp'),
    os.path.join(base, 'frames_crop'),
    os.path.join(base, 'media', 'videos'),
]
for d in temp_dirs:
    if os.path.exists(d):
        try:
            size = 0
            for r, _, fs in os.walk(d):
                for f in fs:
                    fp = os.path.join(r, f)
                    if os.path.isfile(fp):
                        size += os.path.getsize(fp)
            shutil.rmtree(d)
            cleaned += size
            print(f"  Cleaned: {d.replace(base+'\\', '')} ({size/1024/1024:.1f} MB)")
        except Exception as e:
            print(f"  Failed: {d} - {e}")

# 3. 清理旧日志
print("\n[3] 清理旧日志")
log_dir = os.path.join(base, 'logs')
if os.path.exists(log_dir):
    cutoff = datetime.now() - timedelta(days=7)
    for f in os.listdir(log_dir):
        fp = os.path.join(log_dir, f)
        if os.path.isfile(fp):
            mtime = datetime.fromtimestamp(os.path.getmtime(fp))
            if mtime < cutoff:
                try:
                    size = os.path.getsize(fp)
                    os.remove(fp)
                    cleaned += size
                    print(f"  Removed: {f} ({size/1024:.0f} KB)")
                except Exception as e:
                    print(f"  Failed: {f} - {e}")

# 4. 检查大文件
print("\n[4] 大文件 (>50MB)")
large_files = []
for root, dirs, files in os.walk(base):
    if any(x in root for x in ['.git', 'node_modules', 'agency-agents', 'workspace-archive', 'backup']):
        continue
    for f in files:
        fp = os.path.join(root, f)
        if os.path.isfile(fp):
            size = os.path.getsize(fp)
            if size > 50 * 1024 * 1024:
                large_files.append((fp.replace(base + '\\', ''), size / 1024 / 1024))

large_files.sort(key=lambda x: x[1], reverse=True)
for f, s in large_files[:10]:
    print(f"  {f}: {s:.1f} MB")

# 5. 检查子系统大小
print("\n[5] 子系统大小")
subsystems = ['workspace-investment', 'workspace-baiduagent', 'workspace-maphot', 'workspace-pv', 'workspace-social', 'workspace-math']
for d in subsystems:
    dp = os.path.join(base, d)
    if os.path.exists(dp):
        size = 0
        for r, _, fs in os.walk(dp):
            for f in fs:
                fp = os.path.join(r, f)
                if os.path.isfile(fp):
                    size += os.path.getsize(fp)
        print(f"  {d}: {size/1024/1024/1024:.2f} GB")

# 6. 检查其他大目录
print("\n[6] 其他大目录")
other_dirs = ['agency-agents', 'workspace-archive', 'embeddings', 'lancedb', 'memory']
for d in other_dirs:
    dp = os.path.join(base, d)
    if os.path.exists(dp):
        size = 0
        for r, _, fs in os.walk(dp):
            for f in fs:
                fp = os.path.join(r, f)
                if os.path.isfile(fp):
                    size += os.path.getsize(fp)
        print(f"  {d}: {size/1024/1024/1024:.2f} GB")

# 7. 最终状态
print("\n" + "=" * 60)
disk = psutil.disk_usage('C:\\')
print(f"清理后C盘: {disk.free/1024**3:.1f} GB 可用 ({100-disk.percent}% 空闲)")
print(f"累计清理: {cleaned/1024/1024:.1f} MB")
print("=" * 60)
