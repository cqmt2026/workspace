# -*- coding: utf-8 -*-
"""检查各master文件的电话覆盖率"""
import csv, os, sys
sys.stdout.reconfigure(encoding='utf-8')

d = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'
print("=== Master数据电话覆盖率 ===\n")

for f in sorted(os.listdir(d)):
    if not f.endswith('.csv'):
        continue
    fpath = os.path.join(d, f)
    with open(fpath, encoding='utf-8-sig') as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    if not rows:
        continue
    has_tel = sum(1 for r in rows if r.get('tel','').strip())
    rate = has_tel * 100 // len(rows) if rows else 0
    print(f"{f}: {len(rows)}行, 有电话{has_tel}({rate}%)")
