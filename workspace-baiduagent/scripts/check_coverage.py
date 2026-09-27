#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查低覆盖率行业电话情况"""
import sqlite3
import csv
import os

DB = 'data/baidu_crm.db'
MASTER = 'data/master'

# 低覆盖率行业
low_cov = ['能源环保补充','人力资源','检验检测','软件信息','物流货运',
           '智能制造','食品加工','电子科技','教育培训补充','创新型中小企业']

print("=== CRM中低覆盖率行业电话情况 ===")
conn = sqlite3.connect(DB)
cur = conn.cursor()
for ind in low_cov:
    cur.execute("SELECT COUNT(*) FROM customers WHERE industry=?", (ind,))
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM customers WHERE industry=? AND phone IS NOT NULL AND phone != ''", (ind,))
    hp = cur.fetchone()[0]
    pct = round(hp/total*100,1) if total > 0 else 0
    print(f"  {ind}: {hp}/{total} ({pct}%)")

# complete文件情况
print("\n=== _complete文件情况 ===")
for f in sorted(os.listdir(MASTER)):
    if '_complete' in f:
        rows = list(csv.DictReader(open(os.path.join(MASTER, f), encoding='utf-8-sig')))
        phones = sum(1 for r in rows if r.get('电话','').strip())
        print(f"  {f}: {len(rows)} rows, {phones} with phone ({round(phones/len(rows)*100,1)}%)" if rows else f"  {f}: empty")

conn.close()
