#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从E盘备份恢复子系统
按子系统分类逐一恢复
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
E_BACKUP = Path(r'E:\备份')  # E盘备份路径

# 子系统列表（按主人要求逐一恢复）
SUBSYSTEMS = [
    'workspace-novel',
    'workspace-investment',
    'workspace-social',
    'workspace-math',
    'workspace-weixin',
    'workspace-maphot',
    'workspace-baiduagent',
]

def find_backup_path(subsystem):
    """在E盘查找备份路径"""
    # 尝试多种可能的路径
    possible_paths = [
        E_BACKUP / subsystem,
        E_BACKUP / 'backup' / subsystem,
        E_BACKUP / 'workspace' / subsystem,
        E_BACKUP / '.openclaw' / subsystem,
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # 扫描E盘根目录
    if E_BACKUP.exists():
        for item in E_BACKUP.iterdir():
            if item.name == subsystem:
                return item
    
    return None

def restore_subsystem(subsystem):
    """恢复单个子系统"""
    print(f'\n{"="*70}')
    print(f'【{subsystem}】')
    print(f'{"="*70}')
    
    # 查找备份
    backup_path = find_backup_path(subsystem)
    if not backup_path:
        print(f'❌ E盘中未找到备份: {subsystem}')
        return 0, 0, False
    
    print(f'备份路径: {backup_path}')
    
    # 目标路径
    target_path = BASE / subsystem
    target_path.mkdir(parents=True, exist_ok=True)
    
    # 统计备份文件
    backup_files = list(backup_path.rglob('*'))
    backup_files = [f for f in backup_files if f.is_file()]
    print(f'备份文件数: {len(backup_files)}')
    
    # 统计当前文件
    if target_path.exists():
        current_files = list(target_path.rglob('*'))
        current_files = [f for f in current_files if f.is_file()]
        print(f'当前文件数: {len(current_files)}')
    else:
        current_files = []
        print(f'当前文件数: 0')
    
    # 恢复文件
    restored = 0
    skipped = 0
    errors = 0
    
    for fp in backup_files:
        try:
            rel = fp.relative_to(backup_path)
            dest = target_path / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # 检查是否需要恢复（文件不存在或内容不同）
            if dest.exists():
                if dest.stat().st_size == fp.stat().st_size:
                    skipped += 1
                    continue
            
            shutil.copy2(fp, dest)
            restored += 1
            
        except Exception as e:
            errors += 1
            print(f'  错误: {fp.name}: {e}')
    
    print(f'\n恢复结果:')
    print(f'  新增: {restored}个文件')
    print(f'  跳过: {skipped}个文件（已存在且相同）')
    print(f'  错误: {errors}个')
    
    # 验证恢复结果
    final_files = list(target_path.rglob('*'))
    final_files = [f for f in final_files if f.is_file()]
    print(f'\n验证: 当前共 {len(final_files)} 个文件')
    
    success = errors == 0
    return restored, skipped, success

def create_digital_archive(subsystem):
    """为子系统创建数字档案"""
    print(f'\n创建数字档案...')
    
    archive_dir = BASE / 'workspace' / 'archives' / subsystem
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成档案文件
    archive_file = archive_dir / f'{subsystem}_archive_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    
    # 收集信息
    path = BASE / subsystem
    if not path.exists():
        return
    
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
    
    # 生成档案内容
    content = f'''# {subsystem} 数字档案

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 备份来源: E盘

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
    
    for ext, count in sorted(by_ext.items(), key=lambda x: -x[1])[:10]:
        content += f'| {ext} | {count} |\n'
    
    content += f'''
## 主要目录

| 目录 | 文件数 |
|------|--------|
'''
    
    for dir_name, count in sorted(by_dir.items(), key=lambda x: -x[1])[:15]:
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
    print(f'✅ 档案已创建: {archive_file.name}')

def main():
    print('='*70)
    print('从E盘恢复子系统')
    print('='*70)
    
    # 验证E盘
    if not E_BACKUP.exists():
        print(f'❌ E盘不存在，请确认路径')
        return
    
    print(f'E盘路径: {E_BACKUP}')
    print(f'备份目录: {[d.name for d in E_BACKUP.iterdir() if d.is_dir()][:20]}')
    
    # 逐一恢复
    total_restored = 0
    total_skipped = 0
    failed = []
    
    for subsystem in SUBSYSTEMS:
        restored, skipped, success = restore_subsystem(subsystem)
        total_restored += restored
        total_skipped += skipped
        
        if success:
            # 创建数字档案
            create_digital_archive(subsystem)
        else:
            failed.append(subsystem)
    
    # 总结
    print(f'\n\n{"="*70}')
    print('恢复总结')
    print(f'{"="*70}')
    print(f'成功恢复: {len(SUBSYSTEMS) - len(failed)}个子系统')
    print(f'失败: {len(failed)}个子系统')
    if failed:
        print(f'失败列表: {", ".join(failed)}')
    print(f'\n总计: 新增{total_restored}个文件，跳过{total_skipped}个文件')
    print('='*70)

if __name__ == '__main__':
    main()
