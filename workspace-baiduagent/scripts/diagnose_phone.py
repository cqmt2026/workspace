#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断电话清洗问题"""
import sqlite3
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/baidu_crm.db'

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 检查当前电话分布
print("=== 当前电话分布 ===")
cur.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
has_phone = cur.fetchone()[0]
print(f"有电话: {has_phone} ({round(has_phone/11910*100,1)}%)")

# 抽样检查原始电话格式
print("\n=== 电话样例（前30条）===")
cur.execute("SELECT id, name, phone FROM customers WHERE phone IS NOT NULL AND phone != '' LIMIT 30")
for r in cur.fetchall():
    print(f"  ID:{r[0]} {r[1][:20]} -> {r[2]}")

# 检查被标记为空的电话
print("\n=== 被清空电话的客户样例 ===")
cur.execute("SELECT id, name, source FROM customers WHERE phone = '' AND source LIKE '%高德%' LIMIT 10")
for r in cur.fetchall():
    print(f"  ID:{r[0]} {r[1][:20]} source:{r[2]}")

conn.close()
