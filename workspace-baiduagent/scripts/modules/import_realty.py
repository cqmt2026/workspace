# -*- coding: utf-8 -*-
"""导入房产中介数据到CRM"""
import sys, csv, sqlite3, time
sys.stdout.reconfigure(encoding='utf-8')

rows = csv.DictReader(open('data/master/房产中介_gaode_20260903.csv', encoding='utf-8-sig'))
items = list(rows)
print(f'读取 {len(items)} 条')

conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()
ins = skip = 0
for row in items:
    c.execute('SELECT id FROM customers WHERE name = ?', (row['机构名称'],))
    if c.fetchone():
        skip += 1
        continue
    try:
        c.execute('''
            INSERT INTO customers(name, industry, phone, address, district, lat, lng, source, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['机构名称'], row['机构类别'], row['电话'], row['地址'],
            row['区域'], row['纬度'], row['经度'], '高德POI-房产中介',
            '待联系', time.strftime('%Y-%m-%d %H:%M:%S')
        ))
        ins += c.rowcount
    except Exception as e:
        print(f'错误 {row["机构名称"]}: {e}')
        skip += 1

conn.commit()
conn.close()
print(f'✅ 导入CRM: +{ins}条, 跳过{skip}条')
