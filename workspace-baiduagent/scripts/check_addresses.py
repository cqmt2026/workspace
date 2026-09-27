#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查地址格式并改进区域提取"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/baidu_crm.db'

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 获取无区域但有地址的客户
cur.execute("""
    SELECT id, address, district 
    FROM customers 
    WHERE (district IS NULL OR district = '') 
    AND address IS NOT NULL AND address != ''
    LIMIT 30
""")
rows = cur.fetchall()

print(f"无区域但有地址的客户样例({len(rows)}条):")
print("="*60)
for r in rows:
    print(f"ID:{r[0]} 地址:{r[1][:60]}")

# 检查地址中是否包含区域关键词
conn.close()
