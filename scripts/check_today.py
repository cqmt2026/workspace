import os, glob
from datetime import datetime

ws = 'C:/Users/Administrator/.openclaw/workspace'
today = []
for root, dirs, files in os.walk(ws):
    for f in files:
        fp = os.path.join(root, f)
        mtime = os.path.getmtime(fp)
        dt = datetime.fromtimestamp(mtime)
        if dt.date() == datetime(2026, 7, 25).date():
            rel = os.path.relpath(fp, ws)
            today.append((dt, rel))
today.sort(reverse=True)
print('=== 7/25今天修改的文件 ===')
for d, p in today[:20]:
    print(f'  {d.strftime("%H:%M")}  {p}')
if len(today) > 20:
    print(f'  ... 还有{len(today)-20}个')
