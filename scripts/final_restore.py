#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终恢复方案：从E盘根目录复制
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
E_DRIVE = Path(r'E:')
ARCHIVE_DIR = BASE / 'workspace' / 'archives'

def find_e_backup(subsystem):
    """在E盘查找备份"""
    # 尝试多种路径
    paths_to_check = [
        E_DRIVE / subsystem,
        E_DRIVE / '.openclaw' / subsystem,
        E_DRIVE / '备份' / subsystem,
        E_DRIVE / 'backup' / subsystem,
    ]
    
    for path in paths_to_check:
        if path.exists():
            return path
    
    # 扫描E盘根目录
    if E_DRIVE.exists():
        for item in E_DRIVE.iterdir():
            if item.name == subsystem and item.is_dir():
                return item
    
    return None

def restore_subsystem(subsystem):
    """恢复单个子系统"""
    print(f'\n{"="*70}')
    print(f'【{subsystem}】')
    
    # 查找备份
    backup_path = find_e_backup(subsystem)
    
    if not backup_path:
        print(f'❌ E盘未找到备份')
        return 0, 0
    
    print(f'备份路径: {backup_path}')
    
    # 统计备份文件
    backup_files = list(backup_path.rglob('*'))
    backup_files = [f for f in backup_files if f.is_file()]
    print(f'备份文件数: {len(backup_files)}')
    
    # 目标路径
    target_path = BASE / subsystem
    target_path.mkdir(parents=True, exist_ok=True)
    
    # 统计当前文件
    current_files = list(target_path.rglob('*'))
    current_files = [f for f in current_files if f.is_file()]
    print(f'当前文件数: {len(current_files)}')
    
    # 恢复文件
    restored = 0
    for fp in backup_files:
        rel = fp.relative_to(backup_path)
        dest = target_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # 检查是否需要恢复
        if dest.exists():
            if dest.stat().st_size == fp.stat().st_size:
                continue  # 文件相同，跳过
        
        try:
            shutil.copy2(fp, dest)
            restored += 1
        except Exception as e:
            print(f'  错误: {rel}: {e}')
    
    print(f'✅ 恢复: {restored}个新文件')
    return restored, len(backup_files)

def create_digital_archive(subsystem):
    """创建数字档案"""
    path = BASE / subsystem
    if not path.exists():
        return
    
    archive_dir = ARCHIVE_DIR / subsystem
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # 收集文件信息
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
> 数据来源: E盘备份恢复

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
- 恢复来源: E盘备份
- 恢复文件数: {len(files)}

---

_档案生成: 可悦 🌸_
'''
    
    archive_file.write_text(content, encoding='utf-8')
    print(f'  📄 档案已创建')

def main():
    print('='*70)
    print('最终恢复方案')
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
        if total > 0:
            create_digital_archive(sub)
    
    print(f'\n{"="*70}')
    print(f'总计恢复: {total_restored}个文件')
    print('='*70)

if __name__ == '__main__':
    main()
