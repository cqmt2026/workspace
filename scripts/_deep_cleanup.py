# -*- coding: utf-8 -*-
"""Git 对象压缩 + 深度磁盘清理"""
import os
import subprocess
import shutil
import glob

ws = r'C:\Users\Administrator\.openclaw\workspace'

print("=== 深度磁盘清理 ===")
print()

freed = 0

# 1. 压缩 git 对象
print("1. 压缩 git 对象...")
git_dir = os.path.join(ws, 'backup', 'workspace-git')
if os.path.exists(git_dir):
    os.chdir(git_dir)
    try:
        r = subprocess.run(['git', 'reflog', 'expire', '--expire=now', '--all'],
                          capture_output=True, text=True, timeout=60)
        r = subprocess.run(['git', 'gc', '--prune=now', '--aggressive'],
                          capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            print("  Git GC 完成")
            # 计算压缩后大小
            pack_dir = os.path.join(git_dir, '.git', 'objects', 'pack')
            if os.path.exists(pack_dir):
                new_size = sum(os.path.getsize(f) for f in glob.glob(pack_dir + '/*'))
                print(f"  Pack 目录大小: {new_size//1024//1024}MB")
        else:
            print(f"  Git GC 失败: {r.stderr}")
    except Exception as e:
        print(f"  Git GC 异常: {e}")
else:
    print("  Git 目录不存在，跳过")

# 2. 清理 pip/npm 缓存
print()
print("2. 清理 pip/npm 缓存...")
pip_cache = os.path.join(os.path.expanduser('~'), '.cache', 'pip')
if os.path.exists(pip_cache):
    sz = sum(os.path.getsize(f) for f in glob.glob(pip_cache + '/**/*', recursive=True))
    shutil.rmtree(pip_cache, ignore_errors=True)
    freed += sz
    print(f"  pip 缓存: {sz//1024//1024}MB 已清理")

npm_cache = os.path.join(os.path.expanduser('~'), '.npm')
if os.path.exists(npm_cache):
    sz = sum(os.path.getsize(f) for f in glob.glob(npm_cache + '/**/*', recursive=True))
    shutil.rmtree(npm_cache, ignore_errors=True)
    freed += sz
    print(f"  npm 缓存: {sz//1024//1024}MB 已清理")

# 3. 清理 Python __pycache__
print()
print("3. 清理 __pycache__...")
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

# 4. 清理 Temp 文件
print()
print("4. 清理 Temp 文件...")
temp_dirs = [
    os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp'),
    os.path.join(ws, 'tmp'),
]
for td in temp_dirs:
    if os.path.exists(td):
        try:
            sz = sum(os.path.getsize(f) for f in glob.glob(td + '/**/*', recursive=True) if os.path.isfile(f))
            for f in glob.glob(td + '/*'):
                if os.path.isfile(f):
                    os.remove(f)
            freed += sz
            print(f"  Temp: {sz//1024//1024}MB 已清理")
        except:
            pass

# 5. 检查 C 盘空间
print()
print("="*50)
import shutil
c_drive = shutil.disk_usage('C:')
print(f"释放空间: {freed//1024//1024}MB")
print(f"C盘剩余: {c_drive.free//1024//1024//1024}GB")
print(f"C盘使用率: {c_drive.used/c_drive.total*100:.1f}%")
print(f"状态: {'✅ 正常' if c_drive.free/c_drive.total > 0.15 else '⚠️ 空间不足'}")
