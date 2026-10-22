#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""安全清理脚本"""
import os
import shutil
import sys

def cleanup_path(path, desc):
    """清理指定路径，返回清理大小（MB）"""
    if not os.path.exists(path):
        print(f"  [跳过] {desc}: 路径不存在")
        return 0
    
    try:
        if os.path.isfile(path):
            size = os.path.getsize(path)
            os.remove(path)
            print(f"  [删除] {desc}: {size//1024//1024}MB")
            return size // 1024 // 1024
        elif os.path.isdir(path):
            size = get_dir_size(path)
            shutil.rmtree(path, ignore_errors=True)
            print(f"  [删除] {desc}: {size}MB")
            return size
    except (PermissionError, OSError) as e:
        print(f"  [错误] {desc}: {e}")
    return 0

def get_dir_size(path):
    """计算目录大小（MB）"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except:
                    pass
    except:
        pass
    return total // 1024 // 1024

def clean_temp_files():
    """清理临时文件"""
    print("\n【清理临时文件】")
    temp_paths = [
        (r'C:\Windows\Temp', 'Windows临时'),
        (r'C:\Users\Administrator\AppData\Local\Temp', '用户临时'),
    ]
    total = 0
    for path, desc in temp_paths:
        total += cleanup_path(path, desc)
    return total

def clean_cache_files():
    """清理缓存文件"""
    print("\n【清理缓存文件】")
    cache_paths = [
        (r'C:\Users\Administrator\AppData\Local\Google\Chrome\User Data\Default\Cache\Cache_Data', 'Chrome缓存数据'),
        (r'C:\Users\Administrator\AppData\Local\D3DSCache', 'D3D缓存'),
    ]
    total = 0
    for path, desc in cache_paths:
        total += cleanup_path(path, desc)
    return total

def clean_oneDrive_setup():
    """清理OneDrive安装程序"""
    print("\n【清理OneDrive安装程序】")
    path = r'C:\Users\Administrator\AppData\Local\Microsoft\OneDrive\26.178.0913.0007\OneDriveSetup.exe'
    return cleanup_path(path, 'OneDriveSetup.exe')

if __name__ == "__main__":
    print('=' * 70)
    print('安全清理执行')
    print('=' * 70)
    
    total_cleaned = 0
    
    # 执行各项清理
    total_cleaned += clean_temp_files()
    total_cleaned += clean_cache_files()
    total_cleaned += clean_oneDrive_setup()
    
    print('\n' + '=' * 70)
    print(f'清理完成: 释放 {total_cleaned}MB 空间')
    print('=' * 70)
    
    # 检查C盘剩余空间
    import shutil
    _, _, free = shutil.disk_usage('C:\\')
    print(f'C盘剩余空间: {free // 1024 // 1024 // 1024}GB')
