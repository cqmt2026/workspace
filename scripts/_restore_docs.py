# -*- coding: utf-8 -*-
import os, shutil, hashlib
from datetime import datetime

ws = r'C:\Users\Administrator\.openclaw\workspace'
bk = os.path.join(ws, 'backup', 'full_20260903_214200')

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

print('=== 要恢复的文件 ===')
for f in ['TOOLS.md', 'HEARTBEAT.md']:
    src = os.path.join(bk, f)
    dst = os.path.join(ws, f)
    if os.path.exists(src):
        st = os.stat(src)
        print(f'{f}: 备份存在, {st.st_size} bytes, {datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d")}')
        # 恢复
        shutil.copy2(src, dst)
        print(f'  -> 已恢复到主系统根目录: {os.path.exists(dst)}')
        print(f'  -> MD5: {md5(src)} == {md5(dst)}')
    else:
        print(f'{f}: 备份中也 MISSING（无法恢复）')

print()
print('=== 恢复后确认 ===')
for f in ['TOOLS.md', 'HEARTBEAT.md']:
    p = os.path.join(ws, f)
    if os.path.exists(p):
        print(f'{f}: OK, {os.path.getsize(p)} bytes')
    else:
        print(f'{f}: MISSING')
