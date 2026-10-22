#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""深度扫描AppData目录，找出具体大文件"""
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

def find_large_files(path, min_size_mb=50):
    """查找大于指定大小（MB）的文件"""
    large_files = []
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    size = os.path.getsize(fp)
                    if size > min_size_mb * 1024 * 1024:
                        large_files.append((fp, size // 1024 // 1024))
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass
    return large_files

if __name__ == "__main__":
    base = r'C:\Users\Administrator\AppData'
    
    print('=' * 70)
    print('AppData深度扫描')
    print('=' * 70)
    
    # 一级子目录大小
    print('\n【一级子目录大小】')
    sub_dirs = []
    try:
        for x in os.listdir(base):
            full_path = os.path.join(base, x)
            if os.path.isdir(full_path):
                size = get_dir_size(full_path)
                sub_dirs.append((full_path, size, x))
    except (PermissionError, OSError) as e:
        print(f'错误: {e}')
    
    sub_dirs.sort(key=lambda x: x[1], reverse=True)
    total = sum(x[1] for x in sub_dirs)
    print(f'{"排名":<4} {"目录名":<30} {"大小(MB)":<12} {"占比":<8}')
    print('-' * 70)
    for i, (path, size, name) in enumerate(sub_dirs[:15], 1):
        pct = size / total * 100 if total > 0 else 0
        print(f'{i:<4} {name:<30} {size:<12} {pct:<8.1f}%')
    
    # 查找TOP3目录中的大文件
    print('\n' + '=' * 70)
    print('【TOP3目录中的大文件 (>50MB)】')
    print('=' * 70)
    
    for path, size, name in sub_dirs[:3]:
        print(f'\n【{name}】总大小: {size}MB')
        large_files = find_large_files(path, min_size_mb=50)
        large_files.sort(key=lambda x: x[1], reverse=True)
        
        if not large_files:
            print('  无>50MB的文件')
        else:
            print(f'  发现 {len(large_files)} 个大文件:')
            for fp, fsize in large_files[:15]:
                # 显示相对路径
                rel_path = fp.replace(path, '')
                print(f'    {fsize:>5}MB  {rel_path}')
    
    # 特别检查常见大文件位置
    print('\n' + '=' * 70)
    print('【特别检查：缓存和日志】')
    print('=' * 70)
    
    cache_paths = [
        (r'C:\Users\Administrator\AppData\Local\Microsoft\Windows\Explorer', 'Windows缓存'),
        (r'C:\Users\Administrator\AppData\Local\Temp', '临时文件'),
        (r'C:\Users\Administrator\AppData\Local\D3DSCache', 'D3D缓存'),
        (r'C:\Users\Administrator\AppData\Local\CrashDumps', '崩溃转储'),
    ]
    
    for path, desc in cache_paths:
        if os.path.exists(path):
            size = get_dir_size(path)
            if size > 10:
                print(f'{desc}: {size}MB')
