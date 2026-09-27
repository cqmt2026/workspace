#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出有电话+有地址的企业清单"""
import sqlite3

DB = 'data/baidu_crm.db'
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute('''SELECT industry, name, phone, district, address 
             FROM customers 
             WHERE phone IS NOT NULL 
             AND phone != ""
             AND address IS NOT NULL
             AND address != ""
             ORDER BY id 
             LIMIT 50''')
rows = c.fetchall()
print(f'有电话+有地址企业：{len(rows)}家')
for i, r in enumerate(rows, 1):
    print(f'{i}. {r[0]} | {r[1]} | {r[2]} | {r[3]}')
conn.close()
