#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""计算各目录大小并清理C盘空间"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\Administrator\.openclaw'
workspace = os.path.join(base, 'workspace')

def dir_size(path):
    total = 0
    for dp, dn, fn in os.walk(path):
        for f in fn:
            try:
                total += os.path.getsize(os.path.join(dp, f))
            except:
                pass
    return total

# 1. workspace/archives 大小
print('=== workspace/archives/ 目录大小 ===')
archives = os.path.join(workspace, 'archives')
for item in os.listdir(archives):
    path = os.path.join(archives, item)
    if os.path.isdir(path):
        size = dir_size(path)
        print(f'  {item}/: {size/1024/1024:.1f}MB')

# 2. .openclaw/backup/ 大小
print('\n=== .openclaw/backup/ 目录大小 ===')
backup = os.path.join(base, 'backup')
for item in os.listdir(backup):
    path = os.path.join(backup, item)
    if os.path.isdir(path):
        size = dir_size(path)
        print(f'  {item}/: {size/1024/1024:.1f}MB')

# 3. .openclaw/tmp/ 大小
tmp = os.path.join(base, 'tmp')
if os.path.exists(tmp):
    size = dir_size(tmp)
    print(f'\n.openclaw/tmp/: {size/1024/1024:.1f}MB')

# 4. .openclaw/cache/ 大小
cache = os.path.join(base, 'cache')
if os.path.exists(cache):
    size = dir_size(cache)
    print(f'.openclaw/cache/: {size/1024/1024:.1f}MB')

# 5. .openclaw/cloud_cache/ 大小
cloud_cache = os.path.join(base, 'cloud_cache')
if os.path.exists(cloud_cache):
    size = dir_size(cloud_cache)
    print(f'.openclaw/cloud_cache/: {size/1024/1024:.1f}MB')

# 6. workspace/backup/ 大小
ws_backup = os.path.join(workspace, 'backup')
if os.path.exists(ws_backup):
    size = dir_size(ws_backup)
    print(f'\nworkspace/backup/: {size/1024/1024:.1f}MB')

# 7. session-sqlite-migration-runs
session_sqlite = os.path.join(base, 'session-sqlite-migration-runs')
if os.path.exists(session_sqlite):
    size = dir_size(session_sqlite)
    print(f'.openclaw/session-sqlite-migration-runs/: {size/1024/1024:.1f}MB')

# 8. .openclaw/backups/ (注意和backup不同)
backups = os.path.join(base, 'backups')
if os.path.exists(backups):
    size = dir_size(backups)
    print(f'.openclaw/backups/: {size/1024/1024:.1f}MB')
