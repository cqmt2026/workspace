#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""审查百都系统完整性"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
BAIDU = BASE / 'workspace-baiduagent'

def main():
    print('='*70)
    print('百都系统完整性审查')
    print('='*70)
    
    if not BAIDU.exists():
        print('❌ 目录不存在')
        return
    
    # 1. 文件统计
    all_files = list(BAIDU.rglob('*'))
    files = [f for f in all_files if f.is_file()]
    
    print(f'\n【文件统计】')
    print(f'总文件数: {len(files)}')
    
    by_ext = {}
    for f in files:
        ext = f.suffix.lower() or '(无扩展名)'
        by_ext[ext] = by_ext.get(ext, 0) + 1
    
    for ext, count in sorted(by_ext.items(), key=lambda x: -x[1]):
        print(f'  {ext}: {count}个')
    
    # 2. 目录结构
    print(f'\n【目录结构】')
    dirs = [d for d in BAIDU.iterdir() if d.is_dir() and not d.name.startswith('.')]
    for d in sorted(dirs):
        count = sum(1 for _ in d.rglob('*'))
        print(f'  {d.name}/: {count}个文件')
    
    # 3. 时间分布
    print(f'\n【时间分布】')
    if files:
        times = [datetime.fromtimestamp(f.stat().st_mtime) for f in files]
        earliest = min(times)
        latest = max(times)
        print(f'  最早: {earliest.strftime("%Y-%m-%d %H:%M")}')
        print(f'  最新: {latest.strftime("%Y-%m-%d %H:%M")}')
        print(f'  跨度: {(latest - earliest).days}天')
    
    # 4. 关键文件检查
    print(f'\n【关键文件】')
    key_files = {
        'AGENTS.md': BAIDU / 'AGENTS.md',
        'SOUL.md': BAIDU / 'SOUL.md',
        'scripts/': BAIDU / 'scripts',
        'data/': BAIDU / 'data',
        'docs/': BAIDU / 'docs',
        'clients/': BAIDU / 'clients',
    }
    
    for name, path in key_files.items():
        if path.exists():
            if path.is_dir():
                count = sum(1 for _ in path.rglob('*'))
                print(f'  ✅ {name} ({count}文件)')
            else:
                size = path.stat().st_size
                print(f'  ✅ {name} ({size} bytes)')
        else:
            print(f'  ❌ {name} 缺失')
    
    # 5. Python脚本详情
    print(f'\n【Python脚本详情】')
    py_files = list(BAIDU.rglob('*.py'))
    for f in py_files:
        rel = f.relative_to(BAIDU)
        size = f.stat().st_size
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d')
        print(f'  {rel}: {size} bytes, {mtime}')
    
    # 6. 文档内容抽查
    print(f'\n【文档内容抽查】')
    md_files = list(BAIDU.rglob('*.md'))
    for f in md_files[:3]:
        rel = f.relative_to(BAIDU)
        content = f.read_text(encoding='utf-8', errors='replace')
        lines = len(content.split('\n'))
        print(f'  {rel}: {lines}行, {len(content)}字符')
    
    # 7. 数据文件
    print(f'\n【数据文件】')
    data_files = list((BAIDU / 'data').rglob('*')) if (BAIDU / 'data').exists() else []
    for f in data_files[:10]:
        rel = f.relative_to(BAIDU)
        size = f.stat().st_size
        print(f'  {rel}: {size} bytes')
    
    print('\n' + '='*70)

if __name__ == '__main__':
    main()
