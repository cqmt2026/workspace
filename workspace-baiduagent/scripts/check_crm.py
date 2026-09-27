# -*- coding: utf-8 -*-
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
print(f'CRM总客户: {total}')

cur.execute('SELECT industry, COUNT(*) FROM customers GROUP BY industry ORDER BY COUNT(*) DESC LIMIT 15')
print('\n行业分布(Top15):')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

cur.execute("SELECT COUNT(*) FROM customers WHERE tel IS NOT NULL AND tel != ''")
has_tel = cur.fetchone()[0]
print(f'\n有电话: {has_tel}/{total} ({has_tel*100//total}%)')

conn.close()
