#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从备份恢复缺失文件
注意：需要从最近的备份中恢复
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
BACKUP_PATH = BASE / 'backup'

def find_backups():
    """查找可用的备份"""
    backups = []
    if BACKUP_PATH.exists():
        for item in BACKUP_PATH.iterdir():
            if item.is_dir() and item.name.startswith('workspace'):
                backups.append(item)
    return sorted(backups, reverse=True)

def restore_from_backup(subsystem, backup_path):
    """从备份恢复单个子系统"""
    source = backup_path / subsystem
    target = BASE / subsystem
    
    if not source.exists():
        print(f'  备份中无 {subsystem}')
        return 0
    
    if not target.exists():
        target.mkdir(parents=True)
    
    restored = 0
    for fp in source.rglob('*'):
        if fp.is_file():
            rel = fp.relative_to(source)
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copy2(fp, dest)
                restored += 1
    
    return restored

def main():
    print('='*70)
    print('从备份恢复缺失文件')
    print('='*70)
    
    backups = find_backups()
    if not backups:
        print('❌ 未找到备份目录')
        return
    
    print(f'\n找到 {len(backups)} 个备份:')
    for b in backups[:5]:
        print(f'  {b.name}')
    
    # 使用最新的备份
    latest_backup = backups[0]
    print(f'\n使用备份: {latest_backup.name}')
    
    subsystems = [
        'workspace-math',
        'workspace-investment',
        'workspace-baiduagent',
        'workspace-novel',
        'workspace-social',
        'workspace-weixin',
        'workspace-maphot',
    ]
    
    total_restored = 0
    for sub in subsystems:
        print(f'\n【{sub}】')
        count = restore_from_backup(sub, latest_backup)
        print(f'  恢复: {count}个文件')
        total_restored += count
    
    print(f'\n总计恢复: {total_restored}个文件')
    print('='*70)

if __name__ == '__main__':
    main()
