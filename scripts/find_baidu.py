import os, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

base = Path(r'C:\Users\Administrator\.openclaw')

print('='*70)
print('百都系统相关文件搜索')
print('='*70)

# 1. 搜索所有包含"baidu"或"百都"的文件/目录
print('\n【搜索baidu相关目录】')
baidu_dirs = [d for d in base.iterdir() if 'baidu' in d.name.lower() or '百都' in d.name]
for d in baidu_dirs:
    count = sum(1 for _ in d.rglob('*')) if d.is_dir() else 0
    print(f'  {d.name}: {count} files')

# 2. 检查workspace/下的子目录
print('\n【workspace/下的子目录】')
ws = base / 'workspace'
if ws.exists():
    subdirs = [d for d in ws.iterdir() if d.is_dir() and not d.name.startswith('.')]
    for d in sorted(subdirs)[:30]:
        count = sum(1 for _ in d.rglob('*'))
        print(f'  {d.name}: {count} files')

# 3. 检查是否有遗漏的百都文件
print('\n【搜索百都相关Python脚本】')
baidu_py = list(base.rglob('*baidu*.py')) + list(base.rglob('*百都*.py'))
print(f'  找到 {len(baidu_py)} 个')
for f in baidu_py[:10]:
    print(f'    {f.relative_to(base)}')

# 4. 统计所有子系统
print('\n【所有workspace-*子系统文件统计】')
for item in sorted(base.iterdir()):
    if item.name.startswith('workspace-') and item.is_dir():
        count = sum(1 for _ in item.rglob('*'))
        py_count = len(list(item.rglob('*.py')))
        print(f'  {item.name}: {count} files ({py_count} py)')

print('\n' + '='*70)
