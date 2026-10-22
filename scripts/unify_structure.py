#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一工作空间结构
将所有子系统迁移到根级别独立目录
"""

import sys
import os
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
WS = BASE / 'workspace'

# 需要迁移的嵌套目录
MIGRATIONS = [
    ('workspace-novel', WS / 'workspace-novel', BASE / 'workspace-novel'),
    ('workspace-social', WS / 'workspace-social', BASE / 'workspace-social'),
    ('workspace-weixin', WS / 'workspace-weixin', BASE / 'workspace-weixin'),
    ('workspace-maphot', WS / 'workspace-maphot', BASE / 'workspace-maphot'),
]

def migrate():
    print('='*70)
    print('统一工作空间结构')
    print('='*70)
    
    for name, src, dst in MIGRATIONS:
        print(f'\n【{name}】')
        
        if not src.exists():
            print(f'  ❌ 源目录不存在: {src}')
            continue
        
        if dst.exists():
            print(f'  ⚠️  目标已存在，跳过')
            continue
        
        # 移动目录
        try:
            shutil.move(str(src), str(dst))
            print(f'  ✅ 已迁移: {src} -> {dst}')
        except Exception as e:
            print(f'  ❌ 迁移失败: {e}')
    
    print('\n' + '='*70)
    print('验证新结构')
    print('='*70)
    
    # 验证所有子系统
    subsystems = [
        'workspace-novel',
        'workspace-investment',
        'workspace-social',
        'workspace-math',
        'workspace-weixin',
        'workspace-maphot',
        'workspace-baiduagent',
    ]
    
    for sub in subsystems:
        path = BASE / sub
        if path.exists():
            # 统计
            py_count = len(list(path.rglob('*.py')))
            mp4_count = len(list(path.rglob('*.mp4')))
            print(f'  ✅ {sub}/ ({py_count}py, {mp4_count}mp4)')
        else:
            print(f'  ❌ {sub}/ 不存在')

if __name__ == '__main__':
    migrate()
