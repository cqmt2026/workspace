# -*- coding: utf-8 -*-
"""导出Top 3行业A类客户名单"""
import sqlite3, csv, os

db_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
output_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets\Top3行业A类客户名单_2026-09-19.csv'

conn = sqlite3.connect(db_path)
cur = conn.cursor()

industries = ['医疗器械', '机械装备汽配', '新材料化工']

all_customers = []
for ind in industries:
    cur.execute('''
        SELECT name, phone, industry, tier, address 
        FROM customers 
        WHERE industry=? AND tier="A" 
        ORDER BY id
    ''', (ind,))
    rows = cur.fetchall()
    for r in rows:
        all_customers.append({
            'industry': ind,
            'name': r[0],
            'phone': r[1] if r[1] else '',
            'tier': r[3],
            'address': r[4] if r[4] else ''
        })

conn.close()

# 统计
total = len(all_customers)
with_phone = sum(1 for c in all_customers if c['phone'])
by_industry = {}
for c in all_customers:
    ind = c['industry']
    if ind not in by_industry:
        by_industry[ind] = {'total': 0, 'with_phone': 0}
    by_industry[ind]['total'] += 1
    if c['phone']:
        by_industry[ind]['with_phone'] += 1

print(f"总客户数: {total}")
print(f"有电话数: {with_phone} ({with_phone/total*100:.1f}%)")
print("\n分行业统计:")
for ind, stats in by_industry.items():
    print(f"  {ind}: {stats['total']}家, 有电话{stats['with_phone']}家 ({stats['with_phone']/stats['total']*100:.1f}%)")

# 保存到CSV
with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['industry', 'name', 'phone', 'tier', 'address'])
    writer.writeheader()
    writer.writerows(all_customers)

print(f"\n已保存到: {output_path}")

# 打印前30个有电话的客户
print("\n=== 前30个有电话的客户 ===")
count = 0
for c in all_customers:
    if c['phone'] and count < 30:
        print(f"[{c['industry']}] {c['name']} {c['phone']}")
        count += 1
