#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从备份恢复数学动画脚本
注意：备份是6月11日的，可能不含最新脚本
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
MATH_PATH = BASE / 'workspace-math'
BACKUP_PATH = BASE / 'backup' / 'workspace_DELETED_20260611_105444'

def main():
    print('='*70)
    print('恢复数学动画脚本')
    print('='*70)
    
    # 检查备份是否存在
    if not BACKUP_PATH.exists():
        print(f'\n❌ 备份不存在: {BACKUP_PATH}')
        print('无法恢复')
        return
    
    # 检查备份中的math目录
    backup_math = BACKUP_PATH / 'workspace-math'
    if not backup_math.exists():
        # 尝试其他路径
        backup_math = BACKUP_PATH / 'workspace' / 'workspace-math'
    
    if not backup_math.exists():
        print(f'\n❌ 备份中无workspace-math目录')
        print(f'备份内容:')
        for item in sorted(BACKUP_PATH.iterdir())[:10]:
            print(f'  {item.name}')
        return
    
    print(f'\n备份路径: {backup_math}')
    
    # 统计备份中的文件
    backup_py = list(backup_math.rglob('*.py'))
    backup_mp4 = list(backup_math.rglob('*.mp4'))
    backup_other = [f for f in backup_math.rglob('*') if f.is_file() and f.suffix not in ['.py', '.mp4']]
    
    print(f'\n备份中的文件:')
    print(f'  Python: {len(backup_py)}个')
    print(f'  MP4: {len(backup_mp4)}个')
    print(f'  其他: {len(backup_other)}个')
    
    # 统计当前目录
    current_py = list(MATH_PATH.rglob('*.py'))
    current_mp4 = list(MATH_PATH.rglob('*.mp4'))
    
    print(f'\n当前目录:')
    print(f'  Python: {len(current_py)}个')
    print(f'  MP4: {len(current_mp4)}个')
    
    # 恢复Python脚本
    restored = 0
    skipped = 0
    
    print(f'\n开始恢复Python脚本...')
    for fp in backup_py:
        rel = fp.relative_to(backup_math)
        dest = MATH_PATH / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        if dest.exists():
            # 检查是否相同
            if dest.stat().st_size == fp.stat().st_size:
                skipped += 1
                continue
        
        try:
            shutil.copy2(fp, dest)
            restored += 1
        except Exception as e:
            print(f'  错误: {rel}: {e}')
    
    print(f'\n恢复完成:')
    print(f'  新增: {restored}个')
    print(f'  跳过: {skipped}个（已存在）')
    
    # 验证
    final_py = list(MATH_PATH.rglob('*.py'))
    print(f'\n验证: 当前Python脚本 {len(final_py)}个')
    
    if len(final_py) > 10:
        print('[OK] 恢复成功')
    else:
        print('[WARN]  恢复后脚本仍很少，可能需要手动检查')
    
    print('='*70)

if __name__ == '__main__':
    main()
