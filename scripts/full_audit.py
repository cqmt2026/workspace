#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整审计：列出所有子系统文件和备份状态
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')

def count_files(path):
    """统计文件数"""
    if not path.exists():
        return 0
    return sum(1 for _ in path.rglob('*'))

def count_by_type(path, ext):
    """按扩展名统计"""
    if not path.exists():
        return 0
    return len(list(path.rglob(f'*{ext}')))

def main():
    print('='*70)
    print('系统完整审计报告')
    print(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*70)
    
    # 1. 所有workspace-*目录
    print('\n【一、子系统目录状态】')
    subsystems = []
    for item in sorted(BASE.iterdir()):
        if item.name.startswith('workspace-') and item.is_dir():
            py = count_by_type(item, '.py')
            mp4 = count_by_type(item, '.mp4')
            md = count_by_type(item, '.md')
            total = count_files(item)
            subsystems.append({
                'name': item.name,
                'path': item,
                'total': total,
                'py': py,
                'mp4': mp4,
                'md': md,
            })
            print(f'\n{item.name}/')
            print(f'  总计: {total}个文件')
            print(f'  Python: {py}个')
            print(f'  MP4: {mp4}个')
            print(f'  Markdown: {md}个')
            
            # 列出子目录
            dirs = [d.name for d in item.iterdir() if d.is_dir()]
            if dirs:
                print(f'  子目录: {", ".join(dirs[:10])}')
    
    # 2. 检查backup目录
    print('\n\n【二、备份状态】')
    backup_paths = [
        BASE / 'backup',
        BASE / 'backups',
    ]
    for bp in backup_paths:
        if bp.exists():
            count = count_files(bp)
            print(f'\n{bp.name}/: {count}个文件')
            # 列出子目录
            if bp.is_dir():
                for item in sorted(bp.iterdir())[:10]:
                    if item.is_dir():
                        sub_count = count_files(item)
                        print(f'  {item.name}/: {sub_count}个文件')
        else:
            print(f'\n{bp.name}/: 不存在')
    
    # 3. workspace/下的残留
    print('\n\n【三、workspace/根目录残留检查】')
    ws = BASE / 'workspace'
    if ws.exists():
        residual = [d for d in ws.iterdir() if d.name.startswith('workspace-') and d.is_dir()]
        if residual:
            print(f'⚠️  发现 {len(residual)} 个残留目录:')
            for r in residual:
                count = count_files(r)
                print(f'  {r.name}/: {count}个文件')
        else:
            print('[OK] 无残留目录')
    
    # 4. 总结
    print('\n\n【四、审计总结】')
    total_files = sum(s['total'] for s in subsystems)
    total_mp4 = sum(s['mp4'] for s in subsystems)
    print(f'子系统总数: {len(subsystems)}个')
    print(f'总文件数: {total_files}个')
    print(f'总视频数: {total_mp4}个MP4')
    
    # 检查是否有异常
    anomalies = []
    for s in subsystems:
        if s['total'] == 0:
            anomalies.append(f'{s["name"]}: 空目录')
        elif s['mp4'] > 1000 and s['py'] < 10:
            anomalies.append(f'{s["name"]}: 视频多但脚本少（可能缺失开发文件）')
    
    if anomalies:
        print('\n⚠️  发现异常:')
        for a in anomalies:
            print(f'  - {a}')
    else:
        print('\n✅ 未发现明显异常')
    
    print('\n' + '='*70)

if __name__ == '__main__':
    main()
