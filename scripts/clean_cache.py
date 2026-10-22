# -*- coding: utf-8 -*-
"""清理浏览器和系统缓存"""
import os
import shutil
import psutil

print('=== 开始清理缓存 ===')
freed = 0

# 1. Chrome缓存
chrome_cache = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default', 'Cache')
if os.path.exists(chrome_cache):
    try:
        size = 0
        for root, dirs, files in os.walk(chrome_cache):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    size += os.path.getsize(fp)
                except:
                    pass
        shutil.rmtree(chrome_cache, ignore_errors=True)
        freed += size
        print(f'Chrome缓存: {size/1024**2:.0f}MB')
    except Exception as e:
        print(f'Chrome缓存清理失败: {e}')

# 2. Douyin缓存
douyin_cache = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Douyin', 'Cache')
if os.path.exists(douyin_cache):
    try:
        size = 0
        for root, dirs, files in os.walk(douyin_cache):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    size += os.path.getsize(fp)
                except:
                    pass
        shutil.rmtree(douyin_cache, ignore_errors=True)
        freed += size
        print(f'Douyin缓存: {size/1024**2:.0f}MB')
    except Exception as e:
        print(f'Douyin缓存清理失败: {e}')

# 3. Windows临时文件
win_temp = os.environ.get('TEMP', '')
if os.path.exists(win_temp):
    try:
        size = 0
        for root, dirs, files in os.walk(win_temp):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    size += os.path.getsize(fp)
                except:
                    pass
        shutil.rmtree(win_temp, ignore_errors=True)
        os.makedirs(win_temp, exist_ok=True)
        freed += size
        print(f'Windows临时文件: {size/1024**2:.0f}MB')
    except Exception as e:
        print(f'Windows临时文件清理失败: {e}')

print()
print(f'总计释放: {freed/1024**2:.0f}MB')

# 显示磁盘状态
print()
print('=== 当前磁盘状态 ===')
for d in ['C:', 'D:']:
    disk = psutil.disk_usage(d)
    print(f'{d}: {disk.free/1024**3:.1f}GB ({disk.percent}%)')
