#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细扫描AppData目录，分类可清理项"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_dir_size_safe(path):
    """安全计算目录大小"""
    total = 0
    if not os.path.exists(path):
        return 0
    try:
        for dp, dn, fn in os.walk(path):
            for f in fn:
                try:
                    total += os.path.getsize(os.path.join(dp, f))
                except:
                    pass
    except:
        pass
    return total

def scan_appdata():
    base = r'C:\Users\Administrator\AppData'
    local = os.path.join(base, 'Local')
    roaming = os.path.join(base, 'Roaming')
    
    print("=" * 70)
    print("AppData\\Local - 可清理项目分析")
    print("=" * 70)
    
    # 已知可安全清理的缓存目录
    safe_to_clean = [
        'Temp',
        'D3DSCache',
        'Microsoft\\Windows\\INetCache',
        'npm-cache',
        'pip',
        'CrashDumps',
    ]
    
    local_sizes = []
    if os.path.exists(local):
        for d in os.listdir(local):
            path = os.path.join(local, d)
            if os.path.isdir(path):
                size = get_dir_size_safe(path)
                if size > 10 * 1024 * 1024:  # >10MB
                    local_sizes.append((d, size))
    
    local_sizes.sort(key=lambda x: -x[1])
    
    print("\n📊 Top 20 大目录:")
    for name, size in local_sizes[:20]:
        gb = size / 1024**3
        mb = size / 1024 / 1024
        safe = any(s in name.lower() for s in ['temp', 'cache', 'npm', 'pip', 'crash'])
        flag = '✅可清理' if safe else '⚠️注意'
        print(f"  {name:30s} {mb:>8.1f}MB  {flag}")
    
    print("\n" + "=" * 70)
    print("AppData\\Roaming - 可清理项目分析")
    print("=" * 70)
    
    roaming_sizes = []
    if os.path.exists(roaming):
        for d in os.listdir(roaming):
            path = os.path.join(roaming, d)
            if os.path.isdir(path):
                size = get_dir_size_safe(path)
                if size > 10 * 1024 * 1024:  # >10MB
                    roaming_sizes.append((d, size))
    
    roaming_sizes.sort(key=lambda x: -x[1])
    
    print("\n📊 Top 20 大目录:")
    for name, size in roaming_sizes[:20]:
        gb = size / 1024**3
        mb = size / 1024 / 1024
        # 标记可能安全的
        safe_keywords = ['cache', 'tmp', 'temp', 'log']
        safe = any(k in name.lower() for k in safe_keywords) or name.lower() in ['npm-cache', 'pip']
        flag = '✅可清理' if safe else '⚠️注意'
        print(f"  {name:30s} {mb:>8.1f}MB  {flag}")
    
    # 详细分析几个关键目录
    print("\n" + "=" * 70)
    print("关键目录详情")
    print("=" * 70)
    
    key_dirs = [
        (local, 'Google', 'Chrome数据'),
        (local, 'JianyingPro', '剪映缓存'),
        (local, 'kingsoft', 'WPS缓存'),
        (local, 'Tencent', '腾讯软件'),
        (roaming, 'Tencent', '腾讯Roaming'),
        (roaming, 'npm', 'NPM全局模块'),
        (local, 'npm-cache', 'NPM缓存'),
        (local, 'pip', 'Pip缓存'),
    ]
    
    for base_path, subdir, desc in key_dirs:
        full_path = os.path.join(base_path, subdir)
        if os.path.exists(full_path):
            size = get_dir_size_safe(full_path)
            mb = size / 1024 / 1024
            print(f"\n{desc} ({subdir}/):")
            print(f"  路径: {full_path}")
            print(f"  大小: {mb:.1f}MB ({size/1024**3:.2f}GB)")
            
            # 显示子目录
            try:
                items = os.listdir(full_path)
                sub_sizes = []
                for item in items[:10]:
                    item_path = os.path.join(full_path, item)
                    if os.path.isdir(item_path):
                        sub_size = get_dir_size_safe(item_path)
                        if sub_size > 1024*1024:
                            sub_sizes.append((item, sub_size))
                sub_sizes.sort(key=lambda x: -x[1])
                if sub_sizes:
                    print("  子目录:")
                    for item, sub_size in sub_sizes[:5]:
                        print(f"    {item}: {sub_size/1024/1024:.1f}MB")
            except:
                pass

if __name__ == '__main__':
    scan_appdata()
