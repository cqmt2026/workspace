"""继续清理微信缓存 - 第二批"""
import os
import shutil
from datetime import datetime, timedelta

wechat_path = r'D:\WeChat Files'
archive_path = r'D:\WeChat_Archive'

# 收集剩余过期文件
cutoff = datetime.now() - timedelta(days=30)
old_files = []

for root, dirs, files in os.walk(wechat_path):
    for f in files:
        fp = os.path.join(root, f)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(fp))
            if mtime < cutoff:
                size = os.path.getsize(fp)
                old_files.append((fp, size, mtime))
        except:
            continue

print(f'剩余过期文件: {len(old_files)} 个')
print(f'可释放: {sum(s for _,s,_ in old_files)/1024**3:.2f}GB')

# 按时间分组，移到归档目录
moved = 0
moved_size = 0

for fp, size, mtime in old_files:
    try:
        relpath = os.path.relpath(fp, wechat_path)
        parts = relpath.split(os.sep)
        if len(parts) >= 3:
            year_month = f"{parts[-3]}-{parts[-2]}"
        else:
            year_month = mtime.strftime('%Y-%m')
        
        dest_dir = os.path.join(archive_path, year_month)
        os.makedirs(dest_dir, exist_ok=True)
        
        dest_path = os.path.join(dest_dir, os.path.basename(fp))
        shutil.move(fp, dest_path)
        moved += 1
        moved_size += size
    except:
        pass

print(f'已移动: {moved} 文件, {moved_size/1024**3:.2f}GB')

# 显示当前状态
import psutil
d = psutil.disk_usage('D:')
print(f'D盘: {d.free/1024**3:.1f}GB free / {d.total/1024**3:.1f}GB ({d.percent}% used)')
