# -*- coding: utf-8 -*-
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
print(f'CRM总客户: {total}')

cur.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
has_phone = cur.fetchone()[0]
print(f'有电话: {has_phone}/{total} ({has_phone*100//total}%)')

cur.execute("SELECT COUNT(*) FROM customers WHERE status='待联系'")
pending = cur.fetchone()[0]
print(f'待联系: {pending}')

# 各行业电话覆盖率
print('\n各行业电话覆盖率:')
cur.execute('''
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone
    FROM customers GROUP BY industry ORDER BY total DESC LIMIT 15
''')
for r in cur.fetchall():
    rate = r[2]*100//r[1] if r[1] else 0
    print(f'  {r[0]}: {r[1]}家, 有电话{r[2]}({rate}%)')

conn.close()
