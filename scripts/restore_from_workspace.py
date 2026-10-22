#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 E:\.openclaw\workspace 恢复所有子系统
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
SRC = Path(r'E:\.openclaw\workspace')
ARCHIVE_DIR = BASE / 'workspace' / 'archives'

def restore_all():
    print('='*70)
    print(f'从 {SRC} 恢复子系统')
    print('='*70)
    
    if not SRC.exists():
        print(f'❌ 源目录不存在: {SRC}')
        return
    
    # 列出所有子系统
    items = [d for d in os.listdir(SRC) if os.path.isdir(os.path.join(SRC, d)) and d.startswith('workspace-')]
    print(f'\n发现 {len(items)} 个子系统:')
    for item in sorted(items):
        print(f'  {item}')
    
    total_restored = 0
    
    for subsystem in sorted(items):
        src_path = SRC / subsystem
        dst_path = BASE / subsystem
        
        print(f'\n{"="*70}')
        print(f'【{subsystem}】')
        
        # 统计源文件
        src_files = list(src_path.rglob('*'))
        src_files = [f for f in src_files if f.is_file()]
        print(f'源文件数: {len(src_files)}')
        
        # 创建目标目录
        dst_path.mkdir(parents=True, exist_ok=True)
        
        # 统计当前文件
        if dst_path.exists():
            dst_files = list(dst_path.rglob('*'))
            dst_files = [f for f in dst_files if f.is_file()]
            print(f'当前文件数: {len(dst_files)}')
        else:
            dst_files = []
            print(f'当前文件数: 0')
        
        # 复制文件
        restored = 0
        skipped = 0
        for fp in src_files:
            rel = fp.relative_to(src_path)
            dest = dst_path / rel
            
            if dest.exists():
                if dest.stat().st_size == fp.stat().st_size:
                    skipped += 1
                    continue
            
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(fp, dest)
                restored += 1
            except Exception as e:
                print(f'  错误: {rel}: {e}')
        
        print(f'✅ 恢复: {restored}个新文件, 跳过: {skipped}个相同文件')
        total_restored += restored
        
        # 创建数字档案
        create_archive(subsystem, len(src_files))
    
    print(f'\n{"="*70}')
    print(f'总计恢复: {total_restored}个文件')
    print('='*70)

def create_archive(subsystem, backup_count):
    """创建数字档案"""
    path = BASE / subsystem
    if not path.exists():
        return
    
    archive_dir = ARCHIVE_DIR / subsystem
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    all_files = list(path.rglob('*'))
    files = [f for f in all_files if f.is_file()]
    
    by_ext = {}
    for f in files:
        ext = f.suffix.lower() or '(无扩展名)'
        by_ext[ext] = by_ext.get(ext, 0) + 1
    
    by_dir = {}
    for f in files:
        parent = f.parent.name
        by_dir[parent] = by_dir.get(parent, 0) + 1
    
    archive_file = archive_dir / f'{subsystem}_archive_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    
    content = f'''# {subsystem} 数字档案

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 数据来源: E:\\.openclaw\\workspace\\{subsystem}

---

## 文件统计

- 总文件数: {len(files)}
- Python脚本: {by_ext.get('.py', 0)}个
- Markdown文档: {by_ext.get('.md', 0)}个
- 其他文件: {sum(v for k, v in by_ext.items() if k not in ['.py', '.md'])}个

## 文件类型分布

| 类型 | 数量 |
|------|------|
'''
    
    for ext, count in sorted(by_ext.items(), key=lambda x: -x[1])[:15]:
        content += f'| {ext} | {count} |\n'
    
    content += f'''
## 主要目录

| 目录 | 文件数 |
|------|--------|
'''
    
    for dir_name, count in sorted(by_dir.items(), key=lambda x: -x[1])[:20]:
        content += f'| {dir_name}/ | {count} |\n'
    
    content += f'''
## 恢复记录

- 恢复时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 恢复来源: E:\\.openclaw\\workspace\\{subsystem}
- 备份文件数: {backup_count}
- 恢复后文件数: {len(files)}

---

_档案生成: 可悦 🌸_
'''
    
    archive_file.write_text(content, encoding='utf-8')
    print(f'  📄 档案已创建')

if __name__ == '__main__':
    restore_all()
