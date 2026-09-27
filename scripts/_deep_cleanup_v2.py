# -*- coding: utf-8 -*-
"""深度磁盘清理 - 释放更多空间"""
import os
import shutil
import glob

ws = r'C:\Users\Administrator\.openclaw\workspace'

print("=== 深度磁盘清理 ===")
print()

freed = 0

# 1. 删除 workspace-git（非git仓库，262MB）
print("1. 删除 workspace-git...")
git_dir = os.path.join(ws, 'backup', 'workspace-git')
if os.path.exists(git_dir):
    sz = sum(os.path.getsize(f) for f in glob.glob(git_dir + '/**/*', recursive=True) if os.path.isfile(f))
    shutil.rmtree(git_dir, ignore_errors=True)
    freed += sz
    print(f"  删除: {sz//1024//1024}MB")

# 2. 删除重复视频素材
print()
print("2. 删除重复视频素材...")
dup_videos = [
    r'\workspace-maphot\data\videos\素材\crane_port.mp4',
    r'\workspace-maphot\data\videos\素材\night_port.mp4',
    r'\workspace-maphot\data\videos\素材\shanghai.mp4',
    r'\workspace-maphot\data\videos\素材\上海浦东.mp4',
    r'\workspace-maphot\data\videos\素材\货轮海上.mp4',
    r'\workspace-math\media\tmp_ep210_v_tts.mp4',
    r'\workspace-math\L4-共享\videos\EP210_tmp.mp4',
]
for dv in dup_videos:
    fp = os.path.join(ws, dv.lstrip('\\'))
    if os.path.exists(fp):
        sz = os.path.getsize(fp)
        if sz > 10 * 1024 * 1024:  # >10MB
            os.remove(fp)
            freed += sz
            print(f"  删除: {dv.split('\\')[-1]} ({sz//1024//1024}MB)")

# 3. 清理 backup 目录中的空文件夹
print()
print("3. 清理 backup 空目录...")
backup_dir = os.path.join(ws, 'backup')
if os.path.exists(backup_dir):
    for root, dirs, files in os.walk(backup_dir, topdown=False):
        for d in dirs:
            path = os.path.join(root, d)
            if not os.listdir(path):
                os.rmdir(path)

# 4. 清理 __pycache__
print()
print("4. 清理 __pycache__...")
for d in glob.glob(ws + '/**/__pycache__', recursive=True):
    if '\\backup\\' in d:
        continue
    try:
        sz = sum(os.path.getsize(f) for f in glob.glob(d + '/*'))
        shutil.rmtree(d, ignore_errors=True)
        freed += sz
    except:
        pass
print(f"  __pycache__ 清理完成")

# 5. 检查清理结果
print()
print("="*50)
import shutil as sh
c_drive = sh.disk_usage('C:')
print(f"本次释放: {freed//1024//1024}MB")
print(f"C盘剩余: {c_drive.free//1024//1024//1024}GB")
print(f"C盘使用率: {c_drive.used/c_drive.total*100:.1f}%")
print(f"状态: {'✅ 正常' if c_drive.free/c_drive.total > 0.15 else '⚠️ 空间不足'}")
