#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描C盘超过10GB的目录/文件"""
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

def scan_large_items(path, min_size_gb=10, max_depth=2):
    """扫描大目录/文件"""
    results = []
    if not os.path.exists(path):
        return results
    
    for root, dirs, files in os.walk(path):
        depth = root.replace(path, '').count(os.sep)
        if depth >= max_depth:
            dirs.clear()
            continue
        
        # 检查当前目录
        dir_size = sum(os.path.getsize(os.path.join(root, f)) for f in files)
        if dir_size > min_size_gb * 1024 * 1024 * 1024:
            rel_path = root.replace(path, '') or '/'
            results.append(('dir', rel_path, dir_size))
        
        # 检查大文件
        for f in files:
            try:
                fp = os.path.join(root, f)
                size = os.path.getsize(fp)
                if size > min_size_gb * 1024 * 1024 * 1024:
                    rel_path = fp.replace(path, '')
                    results.append(('file', rel_path, size))
            except:
                pass
    
    return sorted(results, key=lambda x: -x[2])

print("=" * 70)
print("C盘超过10GB的目录/文件扫描")
print("=" * 70)

# 扫描主要目录
scan_paths = [
    r'C:\Users\Administrator',
    r'C:\Program Files',
    r'C:\Program Files (x86)',
    r'C:\Windows',
]

found_big = False
for path in scan_paths:
    items = scan_large_items(path, min_size_gb=10)
    if items:
        found_big = True
        print(f"\n【{path}】")
        for item_type, name, size in items:
            unit = 'GB' if size > 1024*1024*1024 else 'MB'
            size_val = size/1024/1024/1024 if size > 1024*1024*1024 else size/1024/1024
            print(f"  {'[DIR]' if item_type=='dir' else '[FILE]'} {name}: {size_val:.1f}{unit}")

if not found_big:
    print("\n未发现超过10GB的单一目录或文件")
    print("\n=== 次大目录分析（>1GB）===")
    
    # 分析用户目录下的子目录
    user_base = r'C:\Users\Administrator'
    subdirs = [d for d in os.listdir(user_base) if os.path.isdir(os.path.join(user_base, d))]
    
    subdir_sizes = {}
    for d in subdirs:
        path = os.path.join(user_base, d)
        size = get_dir_size(path)
        if size > 1024*1024*1024:  # >1GB
            subdir_sizes[d] = size
    
    if subdir_sizes:
        print("\n用户目录下的工作目录（>1GB）:")
        for d, size in sorted(subdir_sizes.items(), key=lambda x: -x[1]):
            print(f"  {d}: {size/1024/1024/1024:.2f}GB")
    
    # 分析Program Files
    pf_dirs = {}
    for d in ['Program Files', 'Program Files (x86)']:
        path = os.path.join('C:\\', d)
        if os.path.exists(path):
            for subdir in os.listdir(path):
                subdir_path = os.path.join(path, subdir)
                if os.path.isdir(subdir_path):
                    size = get_dir_size(subdir_path)
                    if size > 1024*1024*1024:
                        pf_dirs[f'{d}\\{subdir}'] = size
    
    if pf_dirs:
        print("\nProgram Files下的应用（>1GB）:")
        for d, size in sorted(pf_dirs.items(), key=lambda x: -x[1]):
            print(f"  {d}: {size/1024/1024/1024:.2f}GB")

# 显示磁盘总体状态
print("\n" + "=" * 70)
total, used, free = shutil.disk_usage('C:\\')
print(f"C盘总计: {total/1024**3:.1f}GB, 已用{used/1024**3:.1f}GB, 剩余{free/1024**3:.1f}GB")
print("=" * 70)
