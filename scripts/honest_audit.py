#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诚实审计：对比每个子系统的应有文件和实际文件
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw')

def audit_subsystem(name, path, expected_scripts=None):
    """审计单个子系统"""
    result = {
        'name': name,
        'path': str(path),
        'exists': path.exists(),
        'total_files': 0,
        'python_scripts': 0,
        'markdown_docs': 0,
        'other_files': 0,
        'issues': [],
    }
    
    if not path.exists():
        result['issues'].append('目录不存在')
        return result
    
    # 扫描所有文件
    all_files = list(path.rglob('*'))
    files = [f for f in all_files if f.is_file()]
    result['total_files'] = len(files)
    
    # 分类统计
    py_files = [f for f in files if f.suffix == '.py']
    md_files = [f for f in files if f.suffix == '.md']
    other_files = [f for f in files if f.suffix not in ['.py', '.md']]
    
    result['python_scripts'] = len(py_files)
    result['markdown_docs'] = len(md_files)
    result['other_files'] = len(other_files)
    
    # 检查脚本内容（抽样）
    script_sizes = []
    for f in py_files[:10]:
        script_sizes.append(f.stat().st_size)
    
    # 异常检测
    if len(py_files) == 0:
        result['issues'].append('致命：无Python脚本')
    elif len(py_files) < 5 and result['total_files'] > 100:
        result['issues'].append(f'严重：仅{len(py_files)}个脚本，可能缺失开发文件')
    elif len(py_files) < 10 and result['total_files'] > 500:
        result['issues'].append(f'警告：脚本数({len(py_files)})偏少')
    
    # 检查小文件（可能是空壳）
    if script_sizes and sum(script_sizes) < 5000:
        result['issues'].append(f'警告：脚本总大小<{sum(script_sizes)}bytes，可能不完整')
    
    return result

def main():
    print('='*80)
    print('诚实审计报告')
    print(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*80)
    
    # 定义子系统及其预期脚本数
    subsystems = [
        ('小说系统', BASE / 'workspace-novel', 100),
        ('投资系统', BASE / 'workspace-investment', 10),
        ('自媒体系统', BASE / 'workspace-social', 20),
        ('数学动画', BASE / 'workspace-math', 50),
        ('微信小程序', BASE / 'workspace-weixin', 20),
        ('地图热点', BASE / 'workspace-maphot', 100),
        ('百都系统', BASE / 'workspace-baiduagent', 10),
    ]
    
    critical = []
    warnings = []
    ok = []
    
    for name, path, expected in subsystems:
        result = audit_subsystem(name, path, expected)
        
        print(f'\n{"="*80}')
        print(f'【{name}】')
        print(f'路径: {result["path"]}')
        print(f'{"="*80}')
        
        print(f'\n文件统计:')
        print(f'  总文件: {result["total_files"]}个')
        print(f'  Python脚本: {result["python_scripts"]}个')
        print(f'  Markdown文档: {result["markdown_docs"]}个')
        print(f'  其他文件: {result["other_files"]}个')
        print(f'  预期脚本: {expected}个')
        
        if result['issues']:
            print(f'\n⚠️  问题:')
            for issue in result['issues']:
                print(f'  ❌ {issue}')
            
            if '致命' in issue or '严重' in issue:
                critical.append(f'{name}: {issue}')
            else:
                warnings.append(f'{name}: {issue}')
        else:
            print(f'\n✅ 正常')
            ok.append(name)
    
    # 总结
    print(f'\n\n{"="*80}')
    print('审计总结')
    print(f'{"="*80}')
    
    print(f'\n正常系统 ({len(ok)}个): {", ".join(ok)}')
    
    if warnings:
        print(f'\n⚠️  警告系统 ({len(warnings)}个):')
        for w in warnings:
            print(f'  - {w}')
    
    if critical:
        print(f'\n🚨 临界系统 ({len(critical)}个):')
        for c in critical:
            print(f'  - {c}')
    
    print(f'\n{"="*80}')

if __name__ == '__main__':
    main()
