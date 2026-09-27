# -*- coding: utf-8 -*-
"""导入第二梯队数据到CRM"""
import sys, os, sqlite3, csv, glob
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM customers')
old_count = c.fetchone()[0]
print(f'导入前CRM客户数: {old_count}')

new_count = 0
for fpath in glob.glob('data/master/*_sp.csv'):
    fname = os.path.basename(fpath)
    with open(fpath, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        name = row.get('机构名称','').strip()
        phone = row.get('电话','').strip()
        industry = row.get('机构类别','').strip()
        if not name or len(name) < 2:
            continue
        c.execute("SELECT id FROM customers WHERE name=?", (name,))
        if not c.fetchone():
            c.execute('''INSERT INTO customers (name, industry, tier, phone, source, status, created_at)
                         VALUES (?, ?, 'A', ?, '高德POI+专精特新', '待联系', ?)''',
                      (name, industry, phone, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            new_count += 1

conn.commit()
c.execute('SELECT COUNT(*) FROM customers')
new_total = c.fetchone()[0]
conn.close()

print(f'新增: {new_count} 条')
print(f'导入后CRM客户总数: {new_total}')

# 统计各行业
conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()
c.execute('SELECT industry, COUNT(*) FROM customers GROUP BY industry ORDER BY COUNT(*) DESC')
print('\n=== CRM行业分布 ===')
total = 0
for ind, cnt in c.fetchall():
    print(f'  {ind}: {cnt}')
    total += cnt
print(f'  总计: {total}')
conn.close()
