#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全面扫描C盘空间占用，找出大文件元凶"""
import os
import sys
import shutil

sys.stdout.reconfigure(encoding='utf-8')

def get_dir_size(path):
    """计算目录总大小"""
    total = 0
    if not os.path.exists(path):
        return 0
    for dp, dn, fn in os.walk(path):
        for f in fn:
            try:
                total += os.path.getsize(os.path.join(dp, f))
            except:
                pass
    return total

def scan_large_files(path, min_size_mb=50, max_depth=4):
    """扫描大文件"""
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
print("C盘空间占用分析报告")
print("=" * 70)

# 1. 扫描.userclaw目录
base = r'C:\Users\Administrator\.openclaw'
if os.path.exists(base):
    print(f"\n【{base}】")
    base_size = get_dir_size(base)
    print(f"总大小: {base_size/1024/1024/1024:.2f}GB")
    
    # 子目录大小
    subdirs = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)) and not d.startswith('.')]
    subdir_sizes = {}
    for d in subdirs:
        path = os.path.join(base, d)
        size = get_dir_size(path)
        if size > 10 * 1024 * 1024:  # 只显示>10MB的
            subdir_sizes[d] = size
    
    print("\n子目录大小(>10MB):")
    for d, size in sorted(subdir_sizes.items(), key=lambda x: -x[1])[:15]:
        print(f"  {d}/: {size/1024/1024:.1f}MB")
    
    # 大文件
    large_files = scan_large_files(base, min_size_mb=50)
    if large_files:
        print("\n大文件(>50MB):")
        for fp, size in large_files[:20]:
            rel = fp.replace(base + os.sep, '')
            print(f"  {rel}: {size/1024/1024:.1f}MB")

# 2. 扫描桌面
desktop = r'C:\Users\Administrator\Desktop'
if os.path.exists(desktop):
    print(f"\n【桌面】")
    desktop_size = get_dir_size(desktop)
    print(f"总大小: {desktop_size/1024/1024:.1f}MB")
    large_files = scan_large_files(desktop, min_size_mb=50)
    if large_files:
        print("大文件(>50MB):")
        for fp, size in large_files[:10]:
            print(f"  {os.path.basename(fp)}: {size/1024/1024:.1f}MB")

# 3. 扫描下载目录
downloads = r'C:\Users\Administrator\Downloads'
if os.path.exists(downloads):
    print(f"\n【下载目录】")
    dl_size = get_dir_size(downloads)
    print(f"总大小: {dl_size/1024/1024:.1f}MB")
    large_files = scan_large_files(downloads, min_size_mb=50)
    if large_files:
        print("大文件(>50MB):")
        for fp, size in large_files[:10]:
            print(f"  {os.path.basename(fp)}: {size/1024/1024:.1f}MB")

# 4. 扫描文档目录
docs = r'C:\Users\Administrator\Documents'
if os.path.exists(docs):
    print(f"\n【文档】")
    docs_size = get_dir_size(docs)
    print(f"总大小: {docs_size/1024/1024:.1f}MB")
    large_files = scan_large_files(docs, min_size_mb=50)
    if large_files:
        print("大文件(>50MB):")
        for fp, size in large_files[:10]:
            print(f"  {os.path.basename(fp)}: {size/1024/1024:.1f}MB")

# 5. 磁盘总体状态
print("\n" + "=" * 70)
print("磁盘总体状态")
print("=" * 70)
total, used, free = shutil.disk_usage('C:\\')
print(f"C盘: 总{total/1024**3:.1f}GB, 已用{used/1024**3:.1f}GB, 剩余{free/1024**3:.1f}GB ({used/total*100:.1f}%)")
