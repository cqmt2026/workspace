#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径验证工具
验证写入路径是否符合规范
"""
import os
import sys
from pathlib import Path

def validate_path(file_path):
    """验证文件路径是否符合规范"""
    path = Path(file_path)
    
    # 检查路径是否在允许列表中
    parent_dirs = [p.name for p in path.parents]
    
    valid = False
    reason = ""
    
    if path.name.startswith('下周') or path.name.startswith('明日') or path.name.startswith('今日'):
        if 'assets' in parent_dirs:
            valid = True
            reason = "拨打清单 -> assets/"
    elif path.name.endswith('_复盘.md') or path.name.endswith('_执行记录.md'):
        if 'memory' in parent_dirs and 'logs' in parent_dirs:
            valid = True
            reason = "复盘记录 -> memory/logs/"
        elif '记忆' in parent_dirs:
            valid = True
            reason = "复盘记录 -> 记忆/"
    elif path.name.endswith('_踩坑记录.md') or path.name.endswith('_错误记录.md'):
        if 'corrections' in parent_dirs or 'memory' in parent_dirs:
            valid = True
            reason = "踩坑记录 -> memory/corrections/ 或 记忆/corrections/"
    elif path.suffix in ['.py']:
        if 'scripts' in parent_dirs:
            valid = True
            reason = "脚本文件 -> scripts/"
    elif path.suffix in ['.md']:
        if any(d in parent_dirs for d in ['assets', 'memory', 'knowledge', 'docs']):
            valid = True
            reason = f"文档文件 -> {'/'.join(parent_dirs[-2:])}"
    
    return valid, reason

def main():
    if len(sys.argv) < 2:
        print("用法: python validate_path.py <文件路径>")
        print()
        print("示例:")
        print('  python validate_path.py "assets/下周清单.md"')
        print('  python validate_path.py "memory/logs/复盘.md"')
        sys.exit(1)
    
    file_path = sys.argv[1]
    valid, reason = validate_path(file_path)
    
    print("=" * 60)
    print("[路径验证结果]")
    print("=" * 60)
    print()
    print(f"文件路径: {file_path}")
    print(f"验证结果: {'[通过]' if valid else '[失败]'}")
    print(f"路径说明: {reason}")
    print()
    
    if not valid:
        print("建议路径:")
        print("  - 清单类文件: assets/")
        print("  - 复盘记录: memory/logs/ 或 记忆/")
        print("  - 踩坑记录: memory/corrections/ 或 记忆/corrections/")
        print("  - 脚本文件: scripts/ 或 scripts/core/")
    
    print("=" * 60)
    
    sys.exit(0 if valid else 1)

if __name__ == '__main__':
    main()
