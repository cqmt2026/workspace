#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理浏览器缓存"""
import os
import shutil

print("清理浏览器缓存...")

# Chrome缓存
chrome_cache = r'C:\Users\Administrator\AppData\Local\Google\Chrome\User Data\Default\Cache'
if os.path.exists(chrome_cache):
    try:
        shutil.rmtree(chrome_cache)
        print(f"✓ Chrome缓存已清理")
    except Exception as e:
        print(f"✗ Chrome缓存清理失败: {e}")

# IE缓存
ie_cache = r'C:\Users\Administrator\AppData\Local\Microsoft\Windows\INetCache'
if os.path.exists(ie_cache):
    try:
        shutil.rmtree(ie_cache)
        os.makedirs(ie_cache, exist_ok=True)
        print(f"✓ IE缓存已清理")
    except Exception as e:
        print(f"✗ IE缓存清理失败: {e}")

# 检查C盘空间
import shutil
total, used, free = shutil.disk_usage('C:\\')
print(f"\nC盘: {free/1024**3:.2f}GB 剩余 ({used/total*100:.1f}%已用)")
