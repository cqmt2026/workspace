#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

def get_dir_size(path):
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except:
                    pass
    except:
        pass
    return total // 1024 // 1024

base = r'C:\Users\Administrator'
items = []

for x in os.listdir(base):
    if x.startswith('.'):
        continue
    full_path = os.path.join(base, x)
    if os.path.isdir(full_path):
        size = get_dir_size(full_path)
        items.append((full_path, size, x))

items.sort(key=lambda x: x[1], reverse=True)

print('=' * 70)
print('用户主目录扫描结果')
print('=' * 70)
print(f'{"排名":<4} {"目录名":<35} {"大小(MB)":<12} {"占比":<8}')
print('-' * 70)

total = sum(x[1] for x in items)
for i, (path, size, name) in enumerate(items[:20], 1):
    pct = size / total * 100 if total > 0 else 0
    print(f'{i:<4} {name:<35} {size:<12} {pct:<8.1f}%')

print('-' * 70)
top10_size = sum(x[1] for x in items[:10])
print(f'TOP10累计: {top10_size}MB ({top10_size/total*100:.1f}%)')
print(f'总计: {total}MB')

# 深入分析TOP3
print('\n' + '=' * 70)
print('TOP3目录详细分析')
print('=' * 70)

for path, size, name in items[:3]:
    print(f'\n【{name}】总大小: {size}MB')
    sub_items = []
    try:
        for sub in os.listdir(path):
            sub_path = os.path.join(path, sub)
            if os.path.isdir(sub_path) and not sub.startswith('.'):
                sub_size = get_dir_size(sub_path)
                if sub_size > 5:
                    sub_items.append((sub_path, sub_size, sub))
    except:
        pass
    sub_items.sort(key=lambda x: x[1], reverse=True)
    for sub_path, sub_size, sub_name in sub_items[:10]:
        print(f'  {sub_name}: {sub_size}MB')
