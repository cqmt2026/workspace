# -*- coding: utf-8 -*-
import os, sys

ws = r'C:\Users\Administrator\.openclaw\workspace'

print('=== 清理前：空目录统计 ===')
empties = []
for root, dirs, files in os.walk(ws):
    if not dirs and not files:
        empties.append(root)
print(f'共 {len(empties)} 个空目录')
for e in empties[:15]:
    print(f'  {e.replace(ws, "")}')
if len(empties) > 15:
    print(f'  ... 还有 {len(empties)-15} 个')

print()
print('=== 开始清理 ===')
cleaned = 0
for e in empties:
    try:
        os.rmdir(e)
        cleaned += 1
    except Exception as ex:
        print(f'  跳过 {e}: {ex}')
print(f'已删除 {cleaned}/{len(empties)} 个')

print()
print('=== 清理后：剩余空目录 ===')
remain = []
for root, dirs, files in os.walk(ws):
    if not dirs and not files:
        remain.append(root)
print(f'剩余 {len(remain)} 个')
