"""清理微信缓存 - 使用shutil"""
import os
import shutil
from datetime import datetime

wechat_path = r'D:\WeChat Files'
if not os.path.exists(wechat_path):
    print(f'目录不存在: {wechat_path}')
    exit()

# 收集过期文件
old_files = []
cutoff = datetime.now().timestamp() - 30 * 86400

for root, dirs, files in os.walk(wechat_path):
    for f in files:
        fp = os.path.join(root, f)
        try:
            mtime = os.path.getmtime(fp)
            if mtime < cutoff:
                size = os.path.getsize(fp)
                old_files.append((fp, size))
        except:
            continue

print(f'找到 {len(old_files)} 个过期文件')
print(f'可释放: {sum(s for _,s in old_files)/1024**3:.2f}GB')

# 清理
cleaned = 0
freed = 0
for fp, size in old_files[:500]:  # 先清理500个
    try:
        os.remove(fp)
        cleaned += 1
        freed += size
    except Exception as e:
        pass

print(f'已清理: {cleaned} 文件, 释放 {freed/1024**3:.2f}GB')

# 显示状态
import psutil
d = psutil.disk_usage('D:')
print(f'D盘: {d.free/1024**3:.1f}GB free / {d.total/1024**3:.1f}GB ({d.percent}% used)')
