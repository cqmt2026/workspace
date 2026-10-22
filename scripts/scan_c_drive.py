#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描C盘大文件"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def scan_large_files(path, min_size_mb=50, max_depth=3):
    results = []
    if not os.path.exists(path):
        return results
    
    for root, dirs, files in os.walk(path):
        depth = root.replace(path, '').count(os.sep)
        if depth >= max_depth:
            dirs.clear()
            continue
        
        for f in files:
            try:
                fp = os.path.join(root, f)
                size = os.path.getsize(fp)
                if size > min_size_mb * 1024 * 1024:
                    results.append((fp, size))
            except:
                pass
    
    return sorted(results, key=lambda x: -x[1])

print("=" * 70)
print("C盘大文件扫描 (>50MB)")
print("=" * 70)

scan_paths = [
    r'C:\Users\Administrator',
    r'C:\Program Files',
    r'C:\Program Files (x86)',
]

all_files = []
for path in scan_paths:
    files = scan_large_files(path, min_size_mb=50, max_depth=3)
    all_files.extend(files)
    if files:
        print(f"\n【{path}】")
        for fp, size in files[:10]:
            rel = fp.replace(path, '')
            print(f"  {rel}: {size/1024/1024:.1f}MB")

all_files.sort(key=lambda x: -x[1])
print(f"\n{'=' * 70}")
print(f"总计发现 {len(all_files)} 个大文件")
print(f"前20大文件:")
for fp, size in all_files[:20]:
    print(f"  {fp}: {size/1024/1024:.1f}MB")

import shutil
total, used, free = shutil.disk_usage('C:\\')
print(f"\nC盘总计: {total/1024**3:.1f}GB, 已用{used/1024**3:.1f}GB, 剩余{free/1024**3:.1f}GB")
