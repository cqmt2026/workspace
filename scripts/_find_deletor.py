# -*- coding: utf-8 -*-
"""
调查谁删除了主系统根目录的 TOOLS.md 和 HEARTBEAT.md
思路：
1. 列出 backup/full_20260903_214200/ 中这两个文件的时间点（已确认是 08-28 / 08-26）
2. 找 backup 目录本身是什么时间建立的
3. 找所有可能在 09-03 ~ 09-05 执行过、涉及文件删除/清理的脚本（auto_cleanup / system_maintenance / inspect / slim 等）
4. 检查最近 cron 的日志记录（memory/日志/cron_logs / memory/日志/system-maintenance 等）
5. 看 auto_cleanup / 瘦身脚本的逻辑是不是误删
"""
import os, glob, json
from datetime import datetime

ws = r'C:\Users\Administrator\.openclaw\workspace'
bk = os.path.join(ws, 'backup', 'full_20260903_214200')

print('=== 1. 备份建立时间 ===')
bk_st = os.stat(bk)
print(f'backup/full_20260903_214200: mtime={datetime.fromtimestamp(bk_st.st_mtime).strftime("%Y-%m-%d %H:%M")}')

print()
print('=== 2. TOOLS.md / HEARTBEAT.md 在备份中的元信息 ===')
for f in ['TOOLS.md', 'HEARTBEAT.md']:
    p = os.path.join(bk, f)
    st = os.stat(p)
    print(f'{f}: {os.path.getsize(p)} bytes, mtime={datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")}')

print()
print('=== 3. 查找所有可能的清理脚本（候选） ===')
cands = []
for pattern in ['auto_cleanup*.py', 'system_maintenance*.py', 'inspect*.py', 'slim*.py', 'prune*.py', 'clean*.py', 'check_*.py', '_cleanup*', 'disk*', 'optimize*']:
    for root, dirs, files in os.walk(ws):
        if '\\backup\\' in root or '\\workspace-git\\' in root:
            continue
        for fn in files:
            if fn.lower().startswith(pattern.split('*')[0]) and fn.endswith('.py'):
                if any(k in fn.lower() for k in ['clean', 'clear', 'prune', 'trim', 'slim', 'optimize', 'maintain', 'inspect', 'check']):
                    cands.append(os.path.join(root, fn))
cands = sorted(set(cands))
print(f'找到 {len(cands)} 个候选脚本')
for c in cands[:30]:
    print(f'  {c.replace(ws, "")}')

print()
print('=== 4. 检查最近的 cron 日志 ===')
log_root = os.path.join(ws, 'memory', '日志')
for sub in ['cron_logs', 'system-maintenance', '健康检查', '巡检日志', '清理报告', '系统检查']:
    sp = os.path.join(log_root, sub)
    if os.path.exists(sp):
        items = os.listdir(sp)
        print(f'{sub}: {len(items)} items')
        for it in items[-5:]:
            ip = os.path.join(sp, it)
            if os.path.isfile(ip):
                st = os.stat(ip)
                print(f'  {it} ({datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")}, {st.st_size} bytes)')
    else:
        print(f'{sub}: MISSING')

print()
print('=== 5. 最近一次 cron 失败的 run 日志（挑几个 key 任务） ===')
# 看看有没有 run 日志能定位到具体命令
all_logs = list(glob.glob(log_root + '/**/*.log', recursive=True)) + list(glob.glob(log_root + '/**/*.txt', recursive=True))
print(f'全部 log/txt 文件: {len(all_logs)}')
for lp in all_logs[-20:]:
    st = os.stat(lp)
    print(f'  {datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")} {st.st_size}B  {lp.replace(ws,"")}')
