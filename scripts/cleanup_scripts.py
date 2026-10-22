#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""脚本清理工具 - 归档过期/重复/调试文件"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

BASE = Path(r'C:\Users\Administrator\.openclaw\workspace')
SCRIPTS = BASE / 'scripts'
ARCHIVES = BASE / 'archives'

# 分类目录
BROKEN = ARCHIVES / 'broken'
OLD_90 = ARCHIVES / 'old_90days'
DEBUG = SCRIPTS / 'tmp'

for d in [BROKEN, OLD_90, DEBUG]:
    d.mkdir(parents=True, exist_ok=True)

def parse_version(name):
    """提取版本号，返回 (base_name, version)"""
    m = re.match(r'^(.+?)(?:_v(\d+)|-(\d+))\.py$', name)
    if m:
        g2, g3 = m.group(2), m.group(3)
        return m.group(1), int(g2 if g2 else (g3 if g3 else 0))
    return name, 0

now = datetime.now()
stats = {'broken': [], 'old': [], 'debug': [], 'kept': []}

# Step 1: 重复版本归档
groups = {}
for f in SCRIPTS.glob('*.py'):
    base, ver = parse_version(f.name)
    groups.setdefault(base, []).append((f, ver, f.stat().st_mtime))

for base, items in groups.items():
    if len(items) > 1:
        items.sort(key=lambda x: (-x[1], -x[2]))
        stats['kept'].append(items[0][0].name)
        for f, ver, _ in items[1:]:
            shutil.move(str(f), str(BROKEN / f.name))
            stats['broken'].append(f.name)

# Step 2: 90天未修改归档
for f in list(SCRIPTS.glob('*.py')):
    days = (now - datetime.fromtimestamp(f.stat().st_mtime)).days
    if days > 90:
        shutil.move(str(f), str(OLD_90 / f.name))
        stats['old'].append(f'{f.name}({days}d)')

# Step 3: 调试文件移至tmp
for f in list(SCRIPTS.glob('*.py')):
    if f.name.startswith('test_') or f.name.startswith('debug_'):
        shutil.move(str(f), str(DEBUG / f.name))
        stats['debug'].append(f.name)

# 输出报告
print('=' * 50)
print('脚本清理报告')
print('=' * 50)
print(f'\n【重复版本归档】{len(stats["broken"])}个')
for f in stats['broken']:
    print(f'  {f}')

print(f'\n【90天未修改归档】{len(stats["old"])}个')
for f in stats['old'][:20]:
    print(f'  {f}')
if len(stats['old']) > 20:
    print(f'  ... 还有 {len(stats["old"]) - 20} 个')

print(f'\n【调试文件移至tmp】{len(stats["debug"])}个')
for f in stats['debug']:
    print(f'  {f}')

print(f'\n【当前scripts/剩余】{len(list(SCRIPTS.glob("*.py")))}个')
print(f'【archives/broken/】{len(list(BROKEN.glob("*.py")))}个')
print(f'【archives/old_90days/】{len(list(OLD_90.glob("*.py")))}个')
print(f'【scripts/tmp/】{len(list(DEBUG.glob("*.py")))}个')
