#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系统最终审计"""

import os
import glob
import psutil

base = r'C:\Users\Administrator\.openclaw\workspace'
excluded = ['.git', 'node_modules', 'agency-agents', 'workspace-archive', 'backup', '__pycache__']

print("=" * 60)
print("系统状态审计报告")
print("=" * 60)

# 1. 核心文件
core = ['SOUL.md','MEMORY.md','AGENTS.md','USER.md','IDENTITY.md','TOOLS.md','HEARTBEAT.md','coding-standards.md']
missing = [f for f in core if not os.path.exists(os.path.join(base,f))]
print(f"\n[核心文件] {len(core)-len(missing)}/{len(core)}")
if missing: print(f"  缺失: {missing}")

# 2. 子系统脚本
subs = {'investment':'workspace-investment','maphot':'workspace-maphot','pv':'workspace-pv','social':'workspace-social','math':'workspace-math','baidu':'workspace-baiduagent'}
print(f"\n[子系统脚本]")
for k,v in subs.items():
    dp = os.path.join(base,v)
    cnt = len(glob.glob(os.path.join(dp,'*.py')))+len(glob.glob(os.path.join(dp,'**','*.py'),recursive=True)) if os.path.exists(dp) else 0
    print(f"  {k}: {cnt}")

# 3. 重复脚本
print(f"\n[重复脚本]")
names = {}
for root,dirs,files in os.walk(base):
    if any(x in root for x in excluded): continue
    for f in files:
        if f.endswith('.py'):
            if f not in names: names[f]=[]
            names[f].append(root)
dups = {k:v for k,v in names.items() if len(v)>1}
print(f"  重复名: {len(dups)} 个")

# 4. 磁盘
print(f"\n[磁盘空间]")
for d in ['C:','D:','E:','F:']:
    try:
        u = psutil.disk_usage(d)
        print(f"  {d}: {u.free/1024**3:.1f}GB free ({u.percent}% used)")
    except: pass

# 5. 内存
m = psutil.virtual_memory()
print(f"\n[内存] {m.percent}% used, {m.available/1024**3:.1f}GB available")

# 6. Git
import subprocess
try:
    r = subprocess.run(['git','-C',base,'status','--short'],capture_output=True,text=True,timeout=10)
    cnt = len([l for l in r.stdout.splitlines() if l.strip()])
    print(f"\n[Git] {cnt} uncommitted changes")
except: pass

# 7. Obsidian
obs = r'F:\Obsidian\Jarvis'
if os.path.exists(obs):
    cnt = sum(1 for root,_,files in os.walk(obs) for f in files if f.endswith('.md'))
    print(f"\n[Obsidian] {cnt} markdown files")

print("\n" + "=" * 60)
