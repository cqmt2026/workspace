#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描C盘大文件，找出空间占用元凶"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def scan_directory(path, min_size_mb=10):
    """扫描目录，返回大于min_size_mb的文件和目录"""
    results = {
        'files': [],
        'dirs': {}
    }
    
    if not os.path.exists(path):
        return results
    
    for root, dirs, files in os.walk(path):
        # 累计目录大小
        dir_size = 0
        for d in dirs:
            dir_path = os.path.join(root, d)
            if dir_path not in results['dirs']:
                results['dirs'][dir_path] = 0
            for dp, dn, fn in os.walk(dir_path):
                for f in fn:
                    try:
                        fp = os.path.join(dp, f)
                        results['dirs'][dir_path] += os.path.getsize(fp)
                    except:
                        pass
        
        # 扫描单个文件
        for f in files:
            try:
                fp = os.path.join(root, f)
                size = os.path.getsize(fp)
                if size > min_size_mb * 1024 * 1024:
                    results['files'].append((fp, size))
            except:
                pass
    
    return results

# 扫描关键目录
scan_paths = [
    r'C:\Users\Administrator\.openclaw',
    r'C:\Users\Administrator\.openclaw\workspace',
    r'C:\Users\Administrator\.openclaw\workspace-novel',
    r'C:\Users\Administrator\.openclaw\workspace-investment',
    r'C:\Users\Administrator\.openclaw\workspace-social',
    r'C:\Users\Administrator\.openclaw\workspace-math',
    r'C:\Users\Administrator\.openclaw\workspace-maphot',
    r'C:\Users\Administrator\.openclaw\workspace-baiduagent',
    r'C:\Users\Administrator\.openclaw\workspace-weixin',
]

print("=" * 60)
print("C盘大文件扫描报告")
print("=" * 60)

total_wasted = 0

for path in scan_paths:
    if not os.path.exists(path):
        continue
    
    print(f"\n【{path.split(chr(92))[-1] if chr(92) in path else path}】")
    
    # 计算目录总大小
    total_size = 0
    for dp, dn, fn in os.walk(path):
        for f in fn:
            try:
                total_size += os.path.getsize(os.path.join(dp, f))
            except:
                pass
    
    print(f"  总大小: {total_size/1024/1024:.1f}MB")
    
    # 扫描大文件
    results = scan_directory(path, min_size_mb=5)
    
    if results['files']:
        print(f"  大文件(>5MB):")
        for fp, size in sorted(results['files'], key=lambda x: -x[1])[:10]:
            rel_path = fp.replace(path, '')
            print(f"    {rel_path}: {size/1024/1024:.1f}MB")
            total_wasted += size
    
    # 扫描大目录
    big_dirs = {k: v for k, v in results['dirs'].items() if v > 50 * 1024 * 1024}
    if big_dirs:
        print(f"  大目录(>50MB):")
        for d, size in sorted(big_dirs.items(), key=lambda x: -x[1])[:5]:
            rel_path = d.replace(path, '')
            print(f"    {rel_path}: {size/1024/1024:.1f}MB")

print("\n" + "=" * 60)
print(f"潜在可释放空间: {total_wasted/1024/1024/1024:.2f}GB")
print("=" * 60)
