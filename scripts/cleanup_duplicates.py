#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理重复的嵌套目录
删除 workspace/workspace-* 目录（保留根级别的 workspace-*）
"""

import sys
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')
WS = BASE / 'workspace'

def cleanup():
    print('='*70)
    print('清理重复目录')
    print('='*70)
    
    deleted = []
    
    # 找出所有 workspace/workspace-* 目录
    for item in WS.iterdir():
        if item.name.startswith('workspace-') and item.is_dir():
            # 检查根级别是否也有同名目录
            root_path = BASE / item.name
            if root_path.exists():
                print(f'\n【{item.name}】')
                print(f'  旧: {item}')
                print(f'  新: {root_path}')
                
                # 统计文件数
                old_count = sum(1 for _ in item.rglob('*'))
                new_count = sum(1 for _ in root_path.rglob('*'))
                print(f'  旧目录: {old_count}个文件')
                print(f'  新目录: {new_count}个文件')
                
                # 删除旧目录
                try:
                    shutil.rmtree(item)
                    print(f'  ✅ 已删除旧目录')
                    deleted.append(item.name)
                except Exception as e:
                    print(f'  ❌ 删除失败: {e}')
            else:
                print(f'\n⚠️  {item.name}: 根级别目录不存在，保留')
    
    print('\n' + '='*70)
    print(f'清理完成: 删除 {len(deleted)} 个重复目录')
    print('='*70)
    
    # 最终验证
    print('\n最终验证:')
    for item in sorted(WS.iterdir()):
        if item.name.startswith('workspace-'):
            print(f'  ⚠️  仍存在于 workspace/: {item.name}')
    
    print(f'\n根级别子系统:')
    for item in sorted(BASE.iterdir()):
        if item.name.startswith('workspace-') and item.is_dir():
            count = sum(1 for _ in item.rglob('*'))
            print(f'  ✅ {item.name}/ ({count}文件)')

if __name__ == '__main__':
    cleanup()
