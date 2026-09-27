#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查CRM数据库结构"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'baidu_crm.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("数据库表:", [t[0] for t in tables])

# 查看customers表结构
cursor.execute("PRAGMA table_info(customers);")
columns = cursor.fetchall()
print("\ncustomers表结构:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# 查看数据样例
cursor.execute("SELECT * FROM customers LIMIT 5;")
rows = cursor.fetchall()
print("\n数据样例:")
for row in rows:
    print(row)

# 查看状态分布
cursor.execute("SELECT status, COUNT(*) FROM customers GROUP BY status;")
status_counts = cursor.fetchall()
print("\n状态分布:")
for s, c in status_counts:
    print(f"  {s}: {c}")

conn.close()
