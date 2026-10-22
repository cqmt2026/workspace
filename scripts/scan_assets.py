#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资产扫描器 - 分批处理+断点续传
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
DB_PATH = BASE / 'workspace' / 'data' / 'assets.json'
CHECKPOINT = BASE / 'workspace' / 'data' / '.scan_checkpoint'

BATCH_SIZE = 100  # 每批处理100个文件

def classify(fp):
    """分类"""
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

def load_checkpoint():
    """加载断点"""
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text(encoding='utf-8'))
    return {'scanned': [], 'registered': []}

def save_checkpoint(data):
    """保存断点"""
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

def main():
    print('='*60)
    print('资产扫描器 v1.1')
    print('='*60)
    
    # 加载断点
    cp = load_checkpoint()
    scanned_set = set(cp.get('scanned', []))
    registered_set = set(cp.get('registered', []))
    
    print(f'\n断点恢复: 已扫描{len(scanned_set)}个, 已注册{len(registered_set)}个')
    
    # 收集所有MP4
    print('扫描文件...')
    all_mp4 = list(BASE.rglob('*.mp4'))
    print(f'总计: {len(all_mp4)}个')
    
    # 过滤已扫描的
    pending = [fp for fp in all_mp4 if str(fp) not in scanned_set]
    print(f'待处理: {len(pending)}个')
    
    # 加载或创建数据库
    if DB_PATH.exists():
        db = json.loads(DB_PATH.read_text(encoding='utf-8'))
    else:
        db = {'assets': {}, 'index': {}, 'metadata': {
            'created': datetime.now().isoformat(),
            'version': '1.1',
            'total_assets': 0,
        }}
    
    # 分批处理
    batch_num = 0
    start_time = time.time()
    
    for i in range(0, len(pending), BATCH_SIZE):
        batch = pending[i:i+BATCH_SIZE]
        batch_num += 1
        
        for fp in batch:
            try:
                cat, source = classify(fp)
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
                
                scanned_set.add(str(fp))
                registered_set.add(asset_id)
                
            except Exception as e:
                pass
        
        # 保存断点
        save_checkpoint({'scanned': list(scanned_set), 'registered': list(registered_set)})
        
        # 进度报告
        elapsed = time.time() - start_time
        speed = (i + len(batch)) / elapsed if elapsed > 0 else 0
        print(f'  批次{batch_num}: {i+len(batch)}/{len(pending)} ({speed:.0f}文件/秒)')
    
    # 最终统计
    db['metadata']['total_assets'] = len(db['assets'])
    db['metadata']['last_scan'] = datetime.now().isoformat()
    db['metadata']['scan_duration'] = f"{time.time()-start_time:.1f}秒"
    
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding='utf-8')
    
    # 清理断点
    if CHECKPOINT.exists():
        CHECKPOINT.unlink()
    
    print(f'\n扫描完成:')
    print(f'  耗时: {time.time()-start_time:.1f}秒')
    print(f'  总资产: {len(db["assets"])}')
    print(f'\n分类统计:')
    for cat, assets in sorted(db['index'].items(), key=lambda x: -len(x[1])):
        print(f'  {cat}: {len(assets)}个')

if __name__ == '__main__':
    main()
