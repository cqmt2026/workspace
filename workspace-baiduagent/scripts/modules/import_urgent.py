# -*- coding: utf-8 -*-
"""导入紧急补抓数据到CRM"""
import sys, os, csv, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'baidu_crm.db')
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'master', 'urgent_baidu.csv')

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 读取CSV
with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f'读取 {len(rows)} 条新数据')

# 检查是否已存在
inserted = 0
skipped = 0
for row in rows:
    name = row['机构名称'].strip()
    # 检查是否已存在
    cur.execute("SELECT id FROM customers WHERE name = ?", (name,))
    if cur.fetchone():
        skipped += 1
        continue
    cur.execute("""
        INSERT INTO customers (name, industry, phone, address, district, lat, lng, source, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
    """, (
        name,
        row['机构类别'],
        row['电话'],
        row['地址'],
        row['区域'],
        row['纬度'],
        row['经度'],
        '百度POI紧急补抓',
        '待联系'
    ))
    inserted += cur.rowcount

conn.commit()
print(f'插入: {inserted} 条')
print(f'跳过(已存在): {skipped} 条')

# 验证
cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
print(f'CRM总客户: {total}')

cur.execute('SELECT industry, COUNT(*) FROM customers WHERE source="百度POI紧急补抓" GROUP BY industry')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]} 条')

cur.execute('SELECT industry, COUNT(*) FROM customers WHERE industry IN ("人力资源","软件信息","物流货运") GROUP BY industry')
for r in cur.fetchall():
    cur2 = conn.cursor()
    cur2.execute('SELECT COUNT(*) FROM customers WHERE industry=? AND phone IS NOT NULL AND phone != ""', (r[0],))
    has_phone = cur2.fetchone()[0]
    print(f'  {r[0]}: {r[1]}条总, {has_phone}条有电话({round(has_phone/r[1]*100,1)}%)')

conn.close()
print('\n导入完成!')
