# -*- coding: utf-8 -*-
"""生成房产物业Top30拨打清单"""
import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()

print('=' * 70)
print('【房产中介 Top20 - 有电话优先】')
print('=' * 70)
c.execute('''
    SELECT name, phone, district FROM customers
    WHERE industry = '房产中介' AND phone IS NOT NULL AND phone != ''
    ORDER BY id DESC LIMIT 20
''')
for i, r in enumerate(c.fetchall(), 1):
    print(f'{i}. {r[0]} | {r[1]} | {r[2]}')

print()
print('=' * 70)
print('【物业服务 Top10 - 有电话优先】')
print('=' * 70)
c.execute('''
    SELECT name, phone, district FROM customers
    WHERE industry = '物业服务' AND phone IS NOT NULL AND phone != ''
    ORDER BY id DESC LIMIT 10
''')
for i, r in enumerate(c.fetchall(), 1):
    print(f'{i}. {r[0]} | {r[1]} | {r[2]}')

conn.close()
