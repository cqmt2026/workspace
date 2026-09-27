#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出机械装备汽配Top30拨打清单"""
import sqlite3

DB = 'data/baidu_crm.db'
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute('''SELECT name, phone, contact, address, district 
             FROM customers 
             WHERE industry = "机械装备汽配" 
             ORDER BY id 
             LIMIT 30''')
rows = c.fetchall()
print(f'机械装备汽配 Top30（共{len(rows)}条）:')
for i, r in enumerate(rows, 1):
    print(f'{i}. {r[0]} | 电话:{r[1]} | 联系人:{r[2]} | 区域:{r[4]}')
conn.close()
