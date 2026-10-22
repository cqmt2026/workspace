#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作空间重组脚本
目标：将分散的产出迁移到独立子系统目录
"""

import sys
import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
WS = BASE / 'workspace'

# 重组计划
REORG_PLAN = {
    'math_ep': {
        'source': WS,  # 从workspace/根目录找EP*
        'target': BASE / 'workspace-math' / 'ep',
        'pattern': 'EP*',
        'file_filter': '*.mp4',
    },
    'math_scene': {
        'source': WS,
        'target': BASE / 'workspace-math' / 'scenes',
        'pattern': '*Scene*',
        'file_filter': '*.mp4',
    },
    'math_media': {
        'source': WS,
        'target': BASE / 'workspace-math' / 'media',
        'pattern': 'media',
        'file_filter': '*.mp4',
    },
}

def md5sum(filepath):
    h = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def migrate(plan_key):
    plan = REORG_PLAN[plan_key]
    source = plan['source']
    target = plan['target']
    
    print(f'\n【{plan_key}】')
    print(f'  源: {source}')
    print(f'  目标: {target}')
    
    # 创建目标目录
    target.mkdir(parents=True, exist_ok=True)
    
    # 查找源文件
    import glob
    pattern = str(source / plan['pattern'] / plan['file_filter']) if plan['pattern'] != '*' else str(source / plan['file_filter'])
    files = glob.glob(pattern, recursive=True)
    
    # 如果pattern是具体目录名
    if plan['pattern'] != '*' and plan['pattern'] != '*Scene*':
        src_dir = source / plan['pattern']
        if src_dir.exists():
            files = list(src_dir.rglob(plan['file_filter']))
        else:
            # 尝试通配符
            files = list(source.rglob(f'{plan["pattern"]}[0-9]*/{plan["file_filter"]}'))
    elif plan['pattern'] == '*Scene*':
        files = [f for f in source.rglob(plan['file_filter']) if 'Scene' in f.parent.name]
    
    print(f'  找到 {len(files)} 个文件')
    
    if not files:
        print('  跳过（无文件）')
        return 0, 0
    
    migrated = 0
    skipped = 0
    
    for fp in files:
        try:
            # 生成目标文件名（保留原文件名，加日期前缀）
            date_str = datetime.fromtimestamp(fp.stat().st_mtime).strftime('%Y%m%d')
            dest_name = f"{date_str}_{fp.name}"
            dest_path = target / dest_name
            
            # 如果目标已存在，跳过
            if dest_path.exists():
                skipped += 1
                continue
            
            # 复制文件
            shutil.copy2(fp, dest_path)
            migrated += 1
            
        except Exception as e:
            print(f'  错误: {fp.name}: {e}')
            skipped += 1
    
    print(f'  迁移: {migrated}, 跳过: {skipped}')
    return migrated, skipped

def main():
    print('='*70)
    print('工作空间重组脚本')
    print('='*70)
    
    total_migrated = 0
    total_skipped = 0
    
    for key in REORG_PLAN.keys():
        m, s = migrate(key)
        total_migrated += m
        total_skipped += s
    
    print('\n' + '='*70)
    print(f'重组完成: 迁移{total_migrated}个, 跳过{total_skipped}个')
    print('='*70)
    
    # 更新资产索引
    print('\n更新资产索引...')
    import json
    db_path = BASE / 'workspace' / 'data' / 'assets.json'
    if db_path.exists():
        db = json.loads(db_path.read_text(encoding='utf-8'))
        # 更新路径映射
        for aid, info in db['assets'].items():
            old_path = info.get('path', '')
            for plan_key, plan in REORG_PLAN.items():
                if plan_key in old_path or plan['pattern'] in old_path:
                    # 计算新路径
                    date_str = datetime.fromisoformat(info.get('mtime', datetime.now().isoformat())).strftime('%Y%m%d')
                    new_path = plan['target'] / f"{date_str}_{Path(old_path).name}"
                    if new_path.exists():
                        db['assets'][aid]['stored_path'] = str(new_path)
        db_path.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding='utf-8')
        print('  索引已更新')

if __name__ == '__main__':
    main()
