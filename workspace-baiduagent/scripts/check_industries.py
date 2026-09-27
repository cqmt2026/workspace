# -*- coding: utf-8 -*-
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()
cur.execute("SELECT industry, COUNT(*) FROM customers GROUP BY industry ORDER BY COUNT(*) DESC")
print('=== 当前CRM行业分布 ===')
total = 0
for ind, cnt in cur.fetchall():
    print(f'  {ind}: {cnt}')
    total += cnt
print(f'  总计: {total}')
conn.close()