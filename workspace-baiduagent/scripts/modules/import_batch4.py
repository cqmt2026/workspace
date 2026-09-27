# -*- coding: utf-8 -*-
"""导入第4批补抓数据 + 今日汇总"""
import sys, os, csv, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/baidu_crm.db'
CSV_PATH = 'data/master/batch4_baidu.csv'

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
        row['纬度'], row['经度'], '百度POI补抓4', '待联系'
    ))
    inserted += cur.rowcount

conn.commit()
print(f'插入: {inserted} 条')
print(f'跳过(已存在): {skipped} 条')

# 今日汇总
print('\n===== 2026-08-30 百度补抓汇总 =====')
cur.execute("SELECT source, COUNT(*) FROM customers WHERE source LIKE '百度POI补抓%' OR source LIKE '百度POI紧急%' GROUP BY source")
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]} 条')

cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '百度POI补抓%' OR source LIKE '百度POI紧急%'")
today_total = cur.fetchone()[0]
print(f'\n今日百度补抓总计: {today_total} 条')

cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
has_phone = cur.fetchone()[0]
print(f'CRM总客户: {total:,} 有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)')

conn.close()
print('\n完成!')