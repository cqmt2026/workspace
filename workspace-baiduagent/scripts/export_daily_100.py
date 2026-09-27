# -*- coding: utf-8 -*-
"""导出每天100组客户联系方式"""
import sqlite3, csv, os

db_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
output_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets'

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 获取所有A类客户（按行业分组）
cur.execute('''
    SELECT industry, name, phone, tier, address 
    FROM customers 
    WHERE tier="A" 
    ORDER BY industry, id
''')
rows = cur.fetchall()
conn.close()

# 按行业分组
by_industry = {}
for r in rows:
    ind = r[0]
    if ind not in by_industry:
        by_industry[ind] = []
    by_industry[ind].append({
        'industry': ind,
        'name': r[1],
        'phone': r[2] if r[2] else '',
        'tier': r[3],
        'address': r[4] if r[4] else ''
    })

# 统计
total = len(rows)
with_phone = sum(1 for r in rows if r[2])
print(f"总A类客户: {total}家")
print(f"有电话客户: {with_phone}家 ({with_phone/total*100:.1f}%)")
print(f"\n分行业统计:")
for ind, customers in by_industry.items():
    wp = sum(1 for c in customers if c['phone'])
    print(f"  {ind}: {len(customers)}家, 有电话{wp}家 ({wp/len(customers)*100:.1f}%)")

# 生成7天清单（每天100组）
days = ['周一_0922', '周二_0923', '周三_0924', '周四_0925', '周五_0926', '周六_0927', '周日_0928']
industries = list(by_industry.keys())

# 混合所有客户，按行业均衡分配
all_customers = []
for ind in industries:
    for c in by_industry[ind]:
        all_customers.append(c)

# 打乱顺序（简单实现：按ID排序后交替取）
all_customers_sorted = sorted(all_customers, key=lambda x: (x['industry'], x['name']))

# 分配到天
daily_lists = {day: [] for day in days}
for i, c in enumerate(all_customers_sorted):
    day_idx = i % 7
    day = days[day_idx]
    if len(daily_lists[day]) < 100:
        daily_lists[day].append(c)

# 保存为CSV
for day, customers in daily_lists.items():
    output_path = os.path.join(output_dir, f'每天100客户_{day}.csv')
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['industry', 'name', 'phone', 'tier', 'address'])
        writer.writeheader()
        writer.writerows(customers)
    print(f"\n{day}: {len(customers)}家")

print(f"\n已保存到: {output_dir}")
