#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查数据库结构"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()

# 查看所有表
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("=== 表结构 ===")
for r in cur.fetchall():
    print(f"  {r[0]}")
    cur.execute(f"PRAGMA table_info({r[0]})")
    for col in cur.fetchall():
        print(f"    {col[1]} {col[2]}")

# 检查未分类客户
print("\n=== 未分类客户分布 ===")
cur.execute("""
    SELECT industry, COUNT(*) as total, 
           SUM(CASE WHEN tier IS NULL THEN 1 ELSE 0 END) as unclassified
    FROM customers 
    GROUP BY industry 
    ORDER BY unclassified DESC 
    LIMIT 15
""")
for r in cur.fetchall():
    if r[2] > 0:
        print(f"  {r[0]}: {r[2]}未分类/{r[1]}总")

# 检查未分类客户的来源分布
print("\n=== 未分类客户来源分布 ===")
cur.execute("""
    SELECT source, COUNT(*) 
    FROM customers 
    WHERE tier IS NULL 
    GROUP BY source 
    ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
