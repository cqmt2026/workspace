#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描用户主目录大文件夹"""
import os
import sys

def get_dir_size(path):
    """计算目录大小（MB）"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass
    return total // 1024 // 1024

def scan_top_level(base_path):
    """扫描一级子目录"""
    items = []
    try:
        for x in os.listdir(base_path):
            if x.startswith('.'):
                continue
            full_path = os.path.join(base_path, x)
            if os.path.isdir(full_path):
                size = get_dir_size(full_path)
                items.append((full_path, size, x))
    except (PermissionError, OSError) as e:
        print(f"错误: {e}", file=sys.stderr)
    return items

if __name__ == "__main__":
    base = r"C:\Users\Administrator"
    
    print("=" * 60)
    print(f"扫描目录: {base}")
    print("=" * 60)
    
    items = scan_top_level(base)
    items.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n{'排名':<4} {'目录名':<30} {'大小(MB)':<10} {'占比':<8}")
    print("-" * 60)
    
    total = sum(x[1] for x in items)
    for i, (path, size, name) in enumerate(items[:15], 1):
        pct = size / total * 100 if total > 0 else 0
        print(f"{i:<4} {name:<30} {size:<10} {pct:<8.1f}%")
    
    print("-" * 60)
    print(f"{'总计':<4} {'前15个目录':<30} {sum(x[1] for x in items[:15]):<10} {sum(x[1] for x in items[:15])/total*100 if total > 0 else 0:<8.1f}%")
    print(f"{'全量':<4} {'所有目录':<30} {total:<10} {'100.0':<8}%")
    
    # 深入TOP3分析
    print("\n" + "=" * 60)
    print("深入分析TOP3目录")
    print("=" * 60)
    
    for path, size, name in items[:3]:
        print(f"\n【{name}】({size}MB)")
        try:
            sub_items = []
            for sub in os.listdir(path):
                sub_path = os.path.join(path, sub)
                if os.path.isdir(sub_path) and not sub.startswith('.'):
                    sub_size = get_dir_size(sub_path)
                    if sub_size > 10:  # 只显示>10MB的
                        sub_items.append((sub_path, sub_size, sub))
            sub_items.sort(key=lambda x: x[1], reverse=True)
            for sub_path, sub_size, sub_name in sub_items[:10]:
                print(f"  {sub_name}: {sub_size}MB")
        except (PermissionError, OSError) as e:
            print(f"  无法访问: {e}")
