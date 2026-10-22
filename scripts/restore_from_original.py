#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从原始位置复制恢复子系统
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
WS = BASE / 'workspace'
ARCHIVE_DIR = BASE / 'workspace' / 'archives'

def restore_subsystem(subsystem):
    """从workspace/复制回根级别"""
    src = WS / subsystem
    dst = BASE / subsystem
    
    print(f'\n{"="*70}')
    print(f'【{subsystem}】')
    
    if not src.exists():
        print(f'❌ 原始位置不存在: {src}')
        return 0, 0
    
    # 统计源文件
    src_files = list(src.rglob('*'))
    src_files = [f for f in src_files if f.is_file()]
    print(f'原始位置: {len(src_files)}个文件')
    
    # 检查目标是否已存在
    if dst.exists():
        dst_files = list(dst.rglob('*'))
        dst_files = [f for f in dst_files if f.is_file()]
        print(f'当前目标: {len(dst_files)}个文件')
        
        # 如果目标文件数>=源文件数，跳过
        if len(dst_files) >= len(src_files):
            print(f'⚠️  目标文件数已足够，跳过')
            return 0, len(src_files)
    
    # 创建目标目录
    dst.mkdir(parents=True, exist_ok=True)
    
    # 复制文件
    restored = 0
    for fp in src_files:
        rel = fp.relative_to(src)
        dest = dst / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fp, dest)
        restored += 1
    
    print(f'✅ 恢复: {restored}个文件')
    return restored, len(src_files)

def create_digital_archive(subsystem):
    """创建数字档案"""
    path = BASE / subsystem
    if not path.exists():
        return
    
    archive_dir = ARCHIVE_DIR / subsystem
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # 收集所有文件信息
    all_files = list(path.rglob('*'))
    files = [f for f in all_files if f.is_file()]
    
    # 按类型统计
    by_ext = {}
    for f in files:
        ext = f.suffix.lower() or '(无扩展名)'
        by_ext[ext] = by_ext.get(ext, 0) + 1
    
    # 按目录统计
    by_dir = {}
    for f in files:
        parent = f.parent.name
        by_dir[parent] = by_dir.get(parent, 0) + 1
    
    # 生成档案
    archive_file = archive_dir / f'{subsystem}_archive_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    
    content = f'''# {subsystem} 数字档案

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 数据来源: C盘原始位置恢复

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
- 恢复来源: C盘原始位置 (workspace/{subsystem})
- 恢复文件数: {len(files)}

---

_档案生成: 可悦 🌸_
'''
    
    archive_file.write_text(content, encoding='utf-8')
    print(f'  📄 档案: {archive_file.name}')

def main():
    print('='*70)
    print('从原始位置恢复子系统并建立数字档案')
    print('='*70)
    
    subsystems = [
        'workspace-novel',
        'workspace-investment',
        'workspace-social',
        'workspace-math',
        'workspace-weixin',
        'workspace-maphot',
        'workspace-baiduagent',
    ]
    
    total_restored = 0
    
    for sub in subsystems:
        restored, total = restore_subsystem(sub)
        total_restored += restored
        if restored > 0 or total > 0:
            create_digital_archive(sub)
    
    print(f'\n{"="*70}')
    print(f'总计恢复: {total_restored}个文件')
    print('='*70)

if __name__ == '__main__':
    main()
