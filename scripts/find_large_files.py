#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描C盘大文件，找出空间占用元凶"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def scan_large_files(path, min_size_mb=10, max_depth=3):
    """扫描目录下的大文件"""
    results = []
    if not os.path.exists(path):
        return results
    
    for root, dirs, files in os.walk(path):
        # 限制深度
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

# 扫描主要目录
scan_paths = [
    (r'C:\Users\Administrator\.openclaw\workspace-math', 'workspace-math'),
    (r'C:\Users\Administrator\.openclaw\workspace-maphot', 'workspace-maphot'),
    (r'C:\Users\Administrator\.openclaw\workspace-investment', 'workspace-investment'),
    (r'C:\Users\Administrator\.openclaw\workspace-novel', 'workspace-novel'),
    (r'C:\Users\Administrator\.openclaw\workspace', 'workspace'),
]

print("=" * 70)
print("C盘大文件扫描报告 (>10MB)")
print("=" * 70)

total_found = 0
for path, name in scan_paths:
    if not os.path.exists(path):
        continue
    
    files = scan_large_files(path, min_size_mb=10)
    if files:
        print(f"\n【{name}】")
        for fp, size in files[:10]:
            rel_path = fp.replace(path + os.sep, '')
            print(f"  {rel_path}: {size/1024/1024:.1f}MB")
            total_found += size

print(f"\n{'=' * 70}")
print(f"扫描发现大文件总计: {total_found/1024/1024/1024:.2f}GB")
print("=" * 70)

# 额外检查：.git目录
git_dir = r'C:\Users\Administrator\.openclaw\workspace\.git'
if os.path.exists(git_dir):
    git_size = sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(git_dir) for f in fn)
    print(f"\n.git 历史版本: {git_size/1024/1024:.1f}MB")

# memory目录
memory_dir = r'C:\Users\Administrator\.openclaw\workspace\memory'
if os.path.exists(memory_dir):
    memory_size = sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(memory_dir) for f in fn)
    print(f"memory/ 知识库: {memory_size/1024/1024:.1f}MB")
