"""清理微信缓存 - 释放D盘空间"""
import os
import shutil
import psutil
from datetime import datetime, timedelta

wechat_path = r'D:\WeChat Files\wxid_g7e24sg4kuft21'
archive_path = r'D:\WeChat_Backup'
cutoff = datetime.now() - timedelta(days=60)

# 收集过期文件
files_to_move = []
for root, dirs, files in os.walk(wechat_path):
    for f in files:
        fp = os.path.join(root, f)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(fp))
            if mtime < cutoff:
                size = os.path.getsize(fp)
                files_to_move.append((fp, size, mtime))
        except:
            continue

print(f'找到 {len(files_to_move)} 个过期文件')
print(f'可释放: {sum(s for _,s,_ in files_to_move)/1024**3:.2f}GB')

# 移动文件
moved = 0
freed = 0
for fp, size, mtime in files_to_move:
    try:
        relpath = os.path.relpath(fp, wechat_path)
        dest = os.path.join(archive_path, relpath)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(fp, dest)
        moved += 1
        freed += size
    except:
        pass

print(f'已移动: {moved} 文件, {freed/1024**3:.2f}GB')

# 显示结果
d = psutil.disk_usage('D:')
print(f'D盘: {d.free/1024**3:.1f}GB free ({d.percent}% used)')
