# -*- coding: utf-8 -*-
"""生成有真实电话的客户名单（每天100组）"""
import sqlite3, csv, os, random

db_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
output_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets'

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 获取所有有电话的A类客户
cur.execute('''
    SELECT industry, name, phone, tier, address 
    FROM customers 
    WHERE tier="A" AND phone IS NOT NULL AND phone != ''
    ORDER BY industry, id
''')
rows = cur.fetchall()
conn.close()

print(f"有电话的A类客户总数: {len(rows)}家")

# 按行业统计
by_industry = {}
for r in rows:
    ind = r[0]
    if ind not in by_industry:
        by_industry[ind] = []
    by_industry[ind].append({
        'industry': ind,
        'name': r[1],
        'phone': r[2],
        'tier': r[3],
        'address': r[4] if r[4] else ''
    })

print("\n分行业有电话客户数:")
for ind, customers in sorted(by_industry.items(), key=lambda x: -len(x[1])):
    print(f"  {ind}: {len(customers)}家")

# 筛选GEO重点行业
geo_industries = ['医疗器械', '机械装备汽配', '新材料化工', '环保检测', '检验检测', '智能制造', '自动化设备', '模具', '数控机床', '精密机械', '新能源充电电力', '液压设备']
geo_customers = []
for ind in geo_industries:
    if ind in by_industry:
        geo_customers.extend(by_industry[ind])

print(f"\nGEO重点行业有电话客户: {len(geo_customers)}家")

# 混合其他有电话行业（补充到700组）
other_customers = []
for ind, customers in by_industry.items():
    if ind not in geo_industries:
        other_customers.extend(customers)

print(f"其他行业有电话客户: {len(other_customers)}家")

# 生成7天清单（每天100组，优先GEO行业）
days = ['周一_0922', '周二_0923', '周三_0924', '周四_0925', '周五_0926', '周六_0927', '周日_0928']
daily_lists = {day: [] for day in days}

# 先分配GEO行业客户（均衡分配到7天）
random.shuffle(geo_customers)
for i, c in enumerate(geo_customers):
    day_idx = i % 7
    day = days[day_idx]
    daily_lists[day].append(c)

# 再分配其他行业客户（补充到每天100组）
remaining_slots = {day: 100 - len(daily_lists[day]) for day in days}
random.shuffle(other_customers)
for c in other_customers:
    # 找到还有槽位的当天
    available_days = [day for day, slots in remaining_slots.items() if slots > 0]
    if not available_days:
        break
    day = random.choice(available_days)
    daily_lists[day].append(c)
    remaining_slots[day] -= 1

# 保存为CSV
for day, customers in daily_lists.items():
    output_path = os.path.join(output_dir, f'有电话客户_{day}.csv')
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['industry', 'name', 'phone', 'tier', 'address'])
        writer.writeheader()
        writer.writerows(customers)
    print(f"\n{day}: {len(customers)}家（GEO行业{sum(1 for c in customers if c['industry'] in geo_industries)}家）")

print(f"\n已保存到: {output_dir}")

# 打印周一前20个GEO行业客户
print("\n=== 周一前20个GEO行业客户 ===")
count = 0
for c in daily_lists['周一_0922']:
    if c['industry'] in geo_industries:
        print(f"[{c['industry']}] {c['name']} {c['phone']}")
        count += 1
        if count >= 20:
            break
