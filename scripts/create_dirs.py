#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""创建缺失目录+统一子系统结构"""

import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
WS = BASE / 'workspace'

# 定义每个子系统的标准结构
STRUCTURE = {
    'workspace-novel': {
        'path': WS / 'workspace-novel',
        'dirs': ['scripts', 'output', 'knowledge', 'templates'],
    },
    'workspace-investment': {
        'path': BASE / 'workspace-investment',
        'dirs': ['scripts', 'data', 'models', 'reports'],
    },
    'workspace-social': {
        'path': WS / 'workspace-social',
        'dirs': ['scripts', 'output', 'hot_topics', 'publish'],
    },
    'workspace-math': {
        'path': BASE / 'workspace-math',
        'dirs': ['scripts', 'output', 'ep', 'scenes', 'media'],
    },
    'workspace-weixin': {
        'path': WS / 'workspace-weixin',
        'dirs': ['miniprogram', 'cloud', 'docs', 'scripts'],
    },
    'workspace-maphot': {
        'path': WS / 'workspace-maphot',
        'dirs': ['scripts', 'output', 'data', 'templates'],
    },
    'workspace-baiduagent': {
        'path': BASE / 'workspace-baiduagent',
        'dirs': ['scripts', 'data', 'clients', 'reports'],
    },
}

def create_dirs():
    print('='*70)
    print('创建缺失目录')
    print('='*70)
    
    created = 0
    for name, config in STRUCTURE.items():
        path = config['path']
        print(f'\n【{name}】')
        
        if not path.exists():
            print(f'  ❌ 目录不存在: {path}')
            continue
        
        for subdir in config['dirs']:
            subpath = path / subdir
            if subpath.exists():
                print(f'  ✅ {subdir}/')
            else:
                subpath.mkdir()
                print(f'  ➕ {subdir}/ 已创建')
                created += 1
    
    print(f'\n总计创建: {created}个目录')
    print('='*70)

if __name__ == '__main__':
    create_dirs()
