#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""执行批量资产注册"""

import sys
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
DB_PATH = BASE / 'workspace' / 'data' / 'assets.json'

def classify(fp):
    """分类"""
    rel = fp.relative_to(BASE)
    parts = rel.parts
    if len(parts) > 1 and parts[0] == 'workspace':
        if parts[1].startswith('EP') and parts[1][2:].isdigit():
            return 'math_ep', parts[1]
        if 'Scene' in parts[1]:
            return 'math_scene', parts[1]
        if parts[1] == 'media':
            return 'math_scene', 'media'
        if parts[1] == 'snail-video':
            return 'math_ep', 'snail-video'
        if parts[1] == 'L4-共享':
            return 'shared', 'L4-共享'
    if 'workspace-maphot' in str(rel):
        return 'shared', 'maphot'
    if 'workspace-baiduagent' in str(rel):
        return 'baidu', 'baiduagent'
    return 'other', None

def md5sum(fp):
    h = hashlib.md5()
    with open(fp, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    print('扫描MP4文件...')
    mp4s = list(BASE.rglob('*.mp4'))
    print(f'发现 {len(mp4s)} 个')
    
    # 加载或创建数据库
    if DB_PATH.exists():
        db = json.loads(DB_PATH.read_text(encoding='utf-8'))
    else:
        db = {'assets': {}, 'index': {}, 'metadata': {'created': datetime.now().isoformat(), 'version': '1.0', 'total_assets': 0}}
    
    registered = 0
    skipped = 0
    errors = 0
    
    for fp in mp4s:
        try:
            cat, source = classify(fp)
            date_str = datetime.fromtimestamp(fp.stat().st_mtime).strftime('%Y%m%d')
            asset_id = f"{cat[:2].upper()}_{date_str}_{source}_{fp.stem}"
            
            if asset_id in db['assets']:
                skipped += 1
                continue
            
            asset_info = {
                'id': asset_id,
                'original_path': str(fp),
                'stored_path': str(fp),  # 暂不移动，只建索引
                'category': cat,
                'source': source,
                'hash': md5sum(fp),
                'size': fp.stat().st_size,
                'registered_at': datetime.now().isoformat(),
                'mtime': datetime.fromtimestamp(fp.stat().st_mtime).isoformat(),
            }
            
            db['assets'][asset_id] = asset_info
            
            # 更新索引
            if cat not in db['index']:
                db['index'][cat] = {}
            db['index'][cat][asset_id] = str(fp)
            
            registered += 1
        except Exception as e:
            errors += 1
    
    db['metadata']['total_assets'] = len(db['assets'])
    db['metadata']['last_updated'] = datetime.now().isoformat()
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f'\n注册完成:')
    print(f'  新增: {registered}')
    print(f'  跳过: {skipped}')
    print(f'  错误: {errors}')
    print(f'  总计: {len(db["assets"])}')

if __name__ == '__main__':
    main()
