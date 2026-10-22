#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精确定位所有视频资产"""

import sys
import os
import glob
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')

def main():
    print('='*70)
    print('视频资产精准定位')
    print('='*70)
    
    # 收集所有MP4
    mp4s = list(BASE.rglob('*.mp4'))
    print(f'\n总MP4数: {len(mp4s)}\n')
    
    # 按父目录分组
    by_parent = defaultdict(list)
    for fp in mp4s:
        parent = fp.parent.name
        rel = fp.relative_to(BASE)
        by_parent[parent].append(fp)
    
    # 统计
    print('【按父目录统计】')
    for parent, files in sorted(by_parent.items(), key=lambda x: -len(x[1]))[:20]:
        total_size = sum(f.stat().st_size for f in files)
        print(f'  {parent}: {len(files)}个, {total_size/1024/1024:.1f}MB')
    
    # 详细列出EP系列
    print('\n【EP系列详情】')
    ep_pattern = BASE / 'workspace' / 'EP*'
    ep_dirs = list(BASE.glob('**/EP*'))
    ep_dirs = [d for d in ep_dirs if d.is_dir() and d.name.startswith('EP') and d.name[2:].isdigit()]
    
    print(f'找到 {len(ep_dirs)} 个EP目录')
    for ep_dir in sorted(ep_dirs, key=lambda x: x.name)[-15:]:
        mp4s_in_dir = list(ep_dir.glob('*.mp4'))
        if mp4s_in_dir:
            rel = ep_dir.relative_to(BASE)
            print(f'  {rel}: {len(mp4s_in_dir)}个MP4')
    
    # 场景库目录
    print('\n【场景库目录】')
    scene_dirs = [d for d in BASE.iterdir() if d.is_dir() and 'Scene' in d.name]
    for sd in scene_dirs:
        mp4s_in_dir = list(sd.rglob('*.mp4'))
        if mp4s_in_dir:
            print(f'  {sd.name}: {len(mp4s_in_dir)}个MP4')
    
    # 今日产出
    from datetime import datetime, timedelta
    today = datetime.now().strftime('%Y-%m-%d')
    today_mp4 = [fp for fp in mp4s if datetime.fromtimestamp(fp.stat().st_mtime).strftime('%Y-%m-%d') == today]
    print(f'\n【今日产出 ({today})】')
    print(f'  {len(today_mp4)}个视频')
    for fp in sorted(today_mp4, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
        rel = fp.relative_to(BASE)
        size = fp.stat().st_size
        print(f'    {rel}: {size/1024:.0f}KB')

if __name__ == '__main__':
    main()
