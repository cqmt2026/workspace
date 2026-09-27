# -*- coding: utf-8 -*-
"""导入第二批紧急补抓数据"""
import sys, os, csv, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/baidu_crm.db'
CSV_PATH = 'data/master/urgent_batch2_baidu.csv'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

print(f'读取 {len(rows)} 条数据')

inserted = 0
skipped = 0
for row in rows:
    name = row['机构名称'].strip()
    cur.execute("SELECT id FROM customers WHERE name = ?", (name,))
    if cur.fetchone():
        skipped += 1
        continue
    cur.execute("""
        INSERT INTO customers (name, industry, phone, address, district, lat, lng, source, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
    """, (
        name, row['机构类别'], row['电话'], row['地址'], row['区域'],
        row['纬度'], row['经度'], '百度POI紧急补抓2', '待联系'
    ))
    inserted += cur.rowcount

conn.commit()
print(f'插入: {inserted} 条')
print(f'跳过(已存在): {skipped} 条')

# 验证总数
cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
has_phone = cur.fetchone()[0]

print(f'\nCRM总客户: {total:,}')
print(f'有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)')

# 各行业统计
cur.execute('''
    SELECT industry, COUNT(*) as total, 
           SUM(CASE WHEN phone IS NOT NULL AND phone != "" THEN 1 ELSE 0 END) as has_phone
    FROM customers 
    WHERE industry IN ('检验检测','智能制造','食品加工','广告传媒','人力资源','软件信息','物流货运')
    GROUP BY industry ORDER BY industry
''')
print('\n低覆盖率行业现状:')
for r in cur.fetchall():
    pct = round(r[2]/r[1]*100,1) if r[1] else 0
    print(f'  {r[0]}: {r[1]}条, 电话{r[2]}条({pct}%)')

conn.close()
print('\n导入完成!')
