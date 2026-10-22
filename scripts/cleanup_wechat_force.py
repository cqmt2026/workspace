"""清理微信过期文件 - 强制模式"""
import os
import shutil
from datetime import datetime

wechat_path = r'D:\WeChat Files'
if not os.path.exists(wechat_path):
    print(f'目录不存在: {wechat_path}')
    exit()

# 收集过期文件（30天以上）
cutoff = datetime.now().timestamp() - 30 * 86400
old_files = []

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

# 按大小排序，清理前500个大文件
old_files.sort(key=lambda x: x[1], reverse=True)

cleaned = 0
freed = 0
errors = []

for i, (fp, size) in enumerate(old_files[:500]):
    try:
        os.remove(fp)
        cleaned += 1
        freed += size
        if (i + 1) % 100 == 0:
            print(f'  已清理 {i+1}/500...')
    except Exception as e:
        errors.append((fp, str(e)))

print(f'\n清理完成: {cleaned} 文件')
print(f'释放空间: {freed/1024**3:.2f}GB')

if errors:
    print(f'\n错误 {len(errors)} 个:')
    for fp, err in errors[:5]:
        print(f'  {fp}: {err}')

# 显示当前磁盘状态
import psutil
d = psutil.disk_usage('D:')
print(f'\nD盘当前: {d.free/1024**3:.1f}GB free / {d.total/1024**3:.1f}GB ({d.percent}% used)')
