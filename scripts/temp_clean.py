#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理临时文件并报告磁盘空间"""
import os
import shutil
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

def cleanup_temp(path):
    """清理临时文件，返回清理数量"""
    count = 0
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    count += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                    count += 1
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    return count

if __name__ == "__main__":
    # 检查各目录大小
    dirs = {
        "C:\\Windows\\Temp": "C盘Windows临时",
        "C:\\Users\\Administrator\\AppData\\Local\\Temp": "用户临时",
        "C:\\Users\\Administrator": "用户主目录"
    }
    
    print("=== 目录大小检查 ===")
    for path, name in dirs.items():
        if os.path.exists(path):
            size = get_dir_size(path)
            print(f"{name}: {size}MB")
    
    # 尝试清理临时文件
    print("\n=== 清理临时文件 ===")
    for path in ["C:\\Windows\\Temp", "C:\\Users\\Administrator\\AppData\\Local\\Temp"]:
        if os.path.exists(path):
            try:
                count = cleanup_temp(path)
                print(f"{path}: 清理 {count} 个文件")
            except PermissionError:
                print(f"{path}: 权限不足，跳过")
