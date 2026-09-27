# -*- coding: utf-8 -*-
"""盘点各行业数据量与电话覆盖率，确定补抓优先级"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()

cur.execute('''
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone
    FROM customers
    GROUP BY industry
    ORDER BY total DESC
''')

print(f'{"行业":<14}{"总数":>6}{"有电话":>6}{"覆盖率":>8}')
print('-' * 40)
for r in cur.fetchall():
    ind, total, phone = r[0], r[1], r[2] or 0
    pct = round(phone/total*100, 1) if total else 0
    print(f'{ind:<14}{total:>6}{phone:>6}{str(pct)+"%":>8}')

conn.close()