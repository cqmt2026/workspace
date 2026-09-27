#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出宠物医院Top30拨打清单"""
import sqlite3

DB = 'data/baidu_crm.db'
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute('''SELECT name, phone, district 
             FROM customers 
             WHERE industry = "宠物医院" 
             AND phone IS NOT NULL 
             AND phone != ""
             ORDER BY id 
             LIMIT 30''')
rows = c.fetchall()
print(f'宠物医院有电话企业：{len(rows)}家')
for i, r in enumerate(rows, 1):
    print(f'{i}. {r[0]} | 电话:{r[1]} | 区域:{r[2]}')
conn.close()
