import os, glob
from datetime import datetime

ws = 'C:/Users/Administrator/.openclaw/workspace'
hd = os.path.join(ws, 'workspace-maphot', 'hyperframes-demo')

mp4s = sorted(glob.glob(hd + '/*.mp4'), key=lambda x: os.path.getmtime(x), reverse=True)
print(f'hyperframes-demo MP4: {len(mp4s)}个')
for m in mp4s[:6]:
    sz = os.path.getsize(m) / 1024 / 1024
    mt = datetime.fromtimestamp(os.path.getmtime(m)).strftime('%m-%d %H:%M')
    print(f'  {os.path.basename(m):30s} {sz:.1f}MB  {mt}')

# 检查深圳数据
cfg = os.path.join(ws, 'workspace-maphot', 'scripts', 'config', 'city_shenzhen.json')
if os.path.exists(cfg):
    print(f'\ncity_shenzhen.json: {os.path.getsize(cfg)/1024:.1f}KB')

# pipeline.py状态
pipe = os.path.join(ws, 'workspace-maphot', 'scripts', 'pipeline.py')
if os.path.exists(pipe):
    print(f'pipeline.py: {os.path.getsize(pipe)/1024:.1f}KB')

# hyperframes_template.py
ht = os.path.join(ws, 'workspace-maphot', 'scripts', 'hyperframes_template.py')
if os.path.exists(ht):
    print(f'hyperframes_template.py: {os.path.getsize(ht)/1024:.1f}KB')
