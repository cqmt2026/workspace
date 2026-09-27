# -*- coding: utf-8 -*-
"""磁盘清理脚本 - 释放C盘空间"""
import os
import glob

ws = r'C:\Users\Administrator\.openclaw\workspace'

print("=== 磁盘清理开始 ===")
print()

freed = 0

# 1. 清理临时视频文件 (tmp_*.mp4)
print("1. 清理临时视频文件...")
tmp_files = glob.glob(ws + '/**/tmp_*.mp4', recursive=True)
for f in tmp_files:
    sz = os.path.getsize(f)
    os.remove(f)
    freed += sz
    print(f"  删除: {f.replace(ws, '')} ({sz//1024//1024}MB)")

# 2. 清理重复视频素材
print()
print("2. 清理重复视频素材...")
dup_files = [
    r'\workspace-maphot\data\videos\素材\crane_port.mp4',
    r'\workspace-maphot\data\videos\素材\night_port.mp4',
    r'\workspace-maphot\data\videos\素材\shanghai.mp4',
    r'\workspace-maphot\data\videos\素材\上海浦东.mp4',
    r'\workspace-maphot\data\videos\素材\货轮海上.mp4',
]
for df in dup_files:
    fp = ws + df
    if os.path.exists(fp):
        sz = os.path.getsize(fp)
        # 只删除>50MB的
        if sz > 50 * 1024 * 1024:
            os.remove(fp)
            freed += sz
            print(f"  删除: {df} ({sz//1024//1024}MB)")

# 3. 清理__pycache__
print()
print("3. 清理__pycache__...")
pycache_dirs = glob.glob(ws + '/**/__pycache__', recursive=True)
for d in pycache_dirs[:20]:  # 限制数量
    try:
        import shutil
        sz = sum(os.path.getsize(f) for f in glob.glob(d + '/*'))
        shutil.rmtree(d)
        freed += sz
        print(f"  删除: {d.replace(ws, '')} ({sz//1024}KB)")
    except:
        pass

# 4. 清理备份中的空目录
print()
print("4. 清理备份目录...")
backup_dir = ws + '/backup/full_20260903_214200'
if os.path.exists(backup_dir):
    import shutil
    # 只删除空子目录
    for root, dirs, files in os.walk(backup_dir, topdown=False):
        for d in dirs:
            path = os.path.join(root, d)
            if not os.listdir(path):
                os.rmdir(path)
                print(f"  删除空目录: {path.replace(ws, '')}")

print()
print("="*50)
print(f"共释放: {freed//1024//1024}MB ({freed//1024//1024//1024}GB)")

# 检查C盘空间
import shutil
c_drive = shutil.disk_usage('C:')
print(f"C盘剩余: {c_drive.free//1024//1024//1024}GB")
print(f"C盘使用率: {c_drive.used/c_drive.total*100:.1f}%")
