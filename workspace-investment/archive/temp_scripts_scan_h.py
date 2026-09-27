import os
import sys

keyword_patterns = [
    'invest', 'stock', '证券', '股票', '投资',
    'A股', '基金', '量化', 'finance', 'market',
    'k线', 'K线', 'macd', 'kdj', '趋势', '仓位'
]

root = r'H:/.openclaw'
matches = []

for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = dirnames  # walk all subdirs
    for fname in filenames:
        full = os.path.join(dirpath, fname)
        lname = fname.lower()
        for kw in keyword_patterns:
            if kw.lower() in lname or kw in dirpath:
                size = os.path.getsize(full)
                matches.append((full, size, kw))
                break

print(f'找到 {len(matches)} 个相关文件:')
print()
for path, size, kw in sorted(matches):
    print(f'[{kw}] {path} ({size} bytes)')