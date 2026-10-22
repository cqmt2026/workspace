#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速建立资产索引（不移动文件，只建索引）"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
DB_PATH = BASE / 'workspace' / 'data' / 'assets.json'

def classify(fp):
    rel = fp.relative_to(BASE)
    parts = rel.parts
    if len(parts) > 1 and parts[0] == 'workspace':
        if parts[1].startswith('EP') and parts[1][2:].isdigit():
            return 'math_ep', parts[1]
        if 'Scene' in parts[1]:
            return 'math_scene', parts[1]
        if parts[1] in ['media', 'snail-video']:
            return 'math_ep', parts[1]
        if parts[1] == 'L4-共享':
            return 'shared', 'L4-共享'
    if 'workspace-maphot' in str(rel):
        return 'maphot', 'workspace-maphot'
    if 'workspace-baiduagent' in str(rel):
        return 'baidu', 'workspace-baiduagent'
    return 'other', None

def main():
    print('扫描MP4...')
    mp4s = list(BASE.rglob('*.mp4'))
    print(f'发现 {len(mp4s)} 个\n')
    
    db = {'assets': {}, 'index': {}, 'metadata': {
        'created': datetime.now().isoformat(),
        'version': '1.0',
        'total_assets': 0,
    }}
    
    stats = {}
    for i, fp in enumerate(mp4s):
        try:
            cat, source = classify(fp)
            key = f"{cat}_{source}" if source else cat
            stats[key] = stats.get(key, 0) + 1
            
            # 生成ID（不用哈希，用路径+时间）
            mtime = datetime.fromtimestamp(fp.stat().st_mtime)
            asset_id = f"{cat[:2].upper()}_{mtime.strftime('%Y%m%d%H%M%S')}_{fp.stem}"
            
            db['assets'][asset_id] = {
                'id': asset_id,
                'path': str(fp),
                'category': cat,
                'source': source,
                'size': fp.stat().st_size,
                'mtime': mtime.isoformat(),
                'registered_at': datetime.now().isoformat(),
            }
            
            if cat not in db['index']:
                db['index'][cat] = {}
            db['index'][cat][asset_id] = str(fp)
            
            if (i + 1) % 200 == 0:
                print(f'  进度: {i+1}/{len(mp4s)}')
        except Exception as e:
            pass
    
    db['metadata']['total_assets'] = len(db['assets'])
    db['metadata']['scan_time'] = datetime.now().isoformat()
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f'\n索引建立完成:')
    print(f'  总资产: {len(db["assets"])}')
    print(f'\n分类统计:')
    for k, v in sorted(stats.items(), key=lambda x: -x[1])[:15]:
        print(f'  {k}: {v}个')

if __name__ == '__main__':
    main()
