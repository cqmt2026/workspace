"""扫描C盘大文件（>100MB），只扫描关键目录，跳过系统保护目录"""
import os, sys, time

# 扫描目标目录
target_dirs = [
    # 用户目录
    r'C:\Users\Administrator\AppData\Local',
    r'C:\Users\Administrator\AppData\Roaming',
    r'C:\Users\Administrator\Downloads',
    r'C:\Users\Administrator\Desktop',
    r'C:\Users\Administrator\Documents',
    r'C:\Users\Administrator\.openclaw',
    # 程序目录
    r'C:\Program Files',
    r'C:\Program Files (x86)',
    r'C:\ProgramData',
    # 根目录其他
    r'C:\node_modules',
    r'C:\npm-cache',
    r'C:\temp',
    r'C:\tmp',
]

# 跳过目录
skip_dirs = {
    'Windows', 'WinSxS', 'System32', 'assembly', 'Installer',
    'Microsoft.NET', 'WindowsApps', 'Package Cache',
    '$Recycle.Bin', 'System Volume Information', 'Recovery',
    'PerfLogs', 'Config.Msi',
}

# 跳过目录名
skip_names = {
    'node_modules', '.git', '__pycache__', '.cache',
    'CrashDumps', 'DumpStack', 'DumpFiles',
}

large_files = []
scanned = 0
start = time.time()

for td in target_dirs:
    if not os.path.isdir(td):
        continue
    for root, dirs, files in os.walk(td):
        # 跳过系统目录
        rel = root[len('C:\\'):] if root.startswith('C:\\') else ''
        parts = rel.split(os.sep)
        if parts and parts[0] in skip_dirs:
            dirs.clear()
            continue
        # 跳过已知大目录
        dirs[:] = [d for d in dirs if d not in skip_names]

        scanned += 1
        if scanned % 5000 == 0:
            elapsed = time.time() - start
            print(f'  已扫描 {scanned} 个目录, 耗时 {elapsed:.0f}s, 已发现 {len(large_files)} 个大文件', file=sys.stderr)

        for f in files:
            fp = os.path.join(root, f)
            try:
                if os.path.islink(fp):
                    continue
                size = os.path.getsize(fp)
                if size > 100 * 1024 * 1024:  # >100MB
                    large_files.append((size, fp))
            except:
                pass

# 排序
large_files.sort(reverse=True)

elapsed = time.time() - start
print(f'=== C盘大文件扫描结果 ===')
print(f'扫描目录: {scanned} 个, 耗时: {elapsed:.0f}s')
print(f'大文件(>100MB): {len(large_files)} 个')
print(f'大文件(>500MB): {sum(1 for s,_ in large_files if s > 500*1024*1024)} 个')
print(f'大文件(>1GB):   {sum(1 for s,_ in large_files if s > 1024**3)} 个')
print()

# 分类输出
if large_files:
    print('--- TOP 20 大文件 ---')
    for i, (size, path) in enumerate(large_files[:20], 1):
        gb = size / (1024**3)
        if gb >= 1:
            print(f'{i:2d}. {gb:.2f} GB  {path}')
        else:
            print(f'{i:2d}. {size/1024**2:.0f} MB  {path}')

    print()
    print('--- 按目录分类 ---')
    from collections import defaultdict
    by_dir = defaultdict(list)
    for size, path in large_files:
        d = os.path.dirname(path)
        by_dir[d].append((size, path))

    dir_sorted = sorted(by_dir.items(), key=lambda x: sum(s for s,_ in x[1]), reverse=True)
    for d, files in dir_sorted[:15]:
        total = sum(s for s,_ in files) / (1024**3)
        print(f'\n📁 {d}')
        print(f'   总计: {total:.2f} GB, {len(files)} 个文件')
        for size, fp in sorted(files, reverse=True)[:3]:
            gb = size / (1024**3)
            name = os.path.basename(fp)
            if gb >= 1:
                print(f'   {gb:.2f} GB  {name}')
            else:
                print(f'   {size/1024**2:.0f} MB  {name}')
else:
    print('未发现大文件')