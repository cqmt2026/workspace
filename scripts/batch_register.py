#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量注册现有资产到管理系统"""

import sys
import os
import glob
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
WORKSPACE = BASE / 'workspace'

def classify_asset(filepath):
    """根据路径分类资产"""
    rel = filepath.relative_to(BASE)
    parts = rel.parts
    
    # 数学动画EP系列
    if len(parts) > 1 and parts[0] == 'workspace' and parts[1].startswith('EP') and parts[1][2:].isdigit():
        return 'math_ep', parts[1]
    
    # 数学动画场景库
    if len(parts) > 1 and parts[0] == 'workspace' and 'Scene' in parts[1]:
        return 'math_scene', parts[1]
    
    # media目录
    if len(parts) > 1 and parts[0] == 'workspace' and parts[1] == 'media':
        return 'math_scene', 'media'
    
    # snail-video
    if len(parts) > 1 and parts[0] == 'workspace' and parts[1] == 'snail-video':
        return 'math_ep', 'snail-video'
    
    # L4-共享
    if len(parts) > 1 and parts[0] == 'workspace' and parts[1] == 'L4-共享':
        return 'shared', 'L4-共享'
    
    # workspace-maphot
    if 'workspace-maphot' in str(rel):
        return 'shared', 'maphot'
    
    # workspace-baiduagent
    if 'workspace-baiduagent' in str(rel):
        return 'baidu', 'baiduagent'
    
    return 'other', None

def register_asset(filepath, category, source_name):
    """注册单个资产"""
    from asset_manager import AssetManager
    manager = AssetManager()
    
    # 生成ID
    date_str = datetime.now().strftime('%Y%m%d')
    ext = filepath.suffix
    stem = filepath.stem
    asset_id = f"{category[:2].upper()}_{date_str}_{source_name}_{stem}"
    
    try:
        manager.register(str(filepath), category, custom_id=asset_id)
        return True, asset_id
    except Exception as e:
        return False, str(e)

def main():
    print('='*60)
    print('批量资产注册')
    print('='*60)
    
    # 扫描所有MP4
    mp4_files = list(BASE.rglob('*.mp4'))
    print(f'\n发现 {len(mp4_files)} 个MP4文件')
    
    # 按分类统计
    stats = {}
    registered = 0
    failed = 0
    
    for fp in mp4_files:
        cat, source = classify_asset(fp)
        key = f"{cat}_{source}" if source else cat
        stats[key] = stats.get(key, 0) + 1
        
        success, result = register_asset(fp, cat, source or 'unknown')
        if success:
            registered += 1
        else:
            failed += 1
    
    print(f'\n分类统计:')
    for k, v in sorted(stats.items(), key=lambda x: -x[1])[:15]:
        print(f'  {k}: {v}个')
    
    print(f'\n注册结果: {registered}成功, {failed}失败')
    print('='*60)

if __name__ == '__main__':
    main()
