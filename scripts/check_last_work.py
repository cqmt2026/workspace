import os
from datetime import datetime

ws = 'C:/Users/Administrator/.openclaw/workspace'
yesterday = []
target_date = datetime(2026, 7, 24).date()

for root, dirs, files in os.walk(ws):
    for f in files:
        fp = os.path.join(root, f)
        mtime = os.path.getmtime(fp)
        dt = datetime.fromtimestamp(mtime)
        if dt.date() == target_date:
            rel = os.path.relpath(fp, ws)
            yesterday.append((dt, rel))

yesterday.sort(reverse=True)
print('=== 7/24最后修改的文件 ===')
for d, p in yesterday[:40]:
    print(f'  {d.strftime("%H:%M")}  {p}')

if len(yesterday) > 40:
    print(f'  ... 还有 {len(yesterday)-40} 个文件')

# 检查地图热点子系统产出
maphot_out = os.path.join(ws, 'workspace-maphot', 'scripts', 'output')
if os.path.exists(maphot_out):
    mp4s = [f for f in os.listdir(maphot_out) if f.endswith('.mp4')]
    print(f'\n=== 地图热点MP4产出: {len(mp4s)}个 ===')
    for m in sorted(mp4s, reverse=True)[:5]:
        sz = os.path.getsize(os.path.join(maphot_out, m)) / 1024 / 1024
        print(f'  {m} ({sz:.1f}MB)')
else:
    print('\n地图热点output目录不存在')
