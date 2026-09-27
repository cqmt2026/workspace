# -*- coding: utf-8 -*-
"""生成有真实电话的有效B2B客户名单（7天×100组）"""
import sqlite3
import csv
import os
import random

db_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
output_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets'

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 获取所有A类有电话客户
cur.execute('''
    SELECT industry, name, phone, address, note, id 
    FROM customers 
    WHERE tier="A" 
      AND phone IS NOT NULL 
      AND phone != ''
    ORDER BY id
''')
all_rows = cur.fetchall()

# 关键词过滤
keywords_remove = [
    '门诊部', '诊所', '美容整形', '整形医院', '眼科', '口腔医院', '牙科',
    '美容院', '美甲', '纹绣', '理发店', '发廊',
    '幼儿园', '早教', '托管', '培训班', '补习班',
    '房产中介', '二手房', '租赁', '中介',
    '餐饮', '酒店', '宾馆', '民宿', '农家乐', '饭店', '餐厅', '快餐',
    '母婴', '童装', '玩具', '奶粉', '尿不湿',
    '宠物医院', '宠物店', '宠物美容',
    '足疗', '按摩', '养生', '保健',
    '超市', '便利店', '小卖部', '水果店', '蔬菜店',
    '服装店', '鞋店', '化妆品店', '饰品', '首饰',
    '五金店', '杂货店', '日杂',
    '摄影', '照相', '婚礼', '婚庆',
    '美发', '美容美发', '美甲美睫',
    '图文', '复印', '打印',
]

keywords_keep = ['有限公司', '集团', '公司', '厂', '工厂', '制造', '生产', '实业', '工贸', '科技', '技术', '设备', '机械', '汽车', '电子', '化工', '新材料', '环保', '检测', '能源', '电力', '建设', '工程', '建筑', '建材', '材料', '精密', '自动化', '智能', '新能源', '商贸', '贸易', '批发', '零售', '物流', '运输', '仓储']

valid_rows = []
for r in all_rows:
    name = str(r[1])
    address = str(r[3]) if r[3] else ''
    combined = name + ' ' + address
    
    skip = False
    for kw in keywords_remove:
        if kw in combined:
            skip = True
            break
    if skip:
        continue
    
    keep = False
    for kw in keywords_keep:
        if kw in name:
            keep = True
            break
    if not keep:
        continue
    
    valid_rows.append(r)

print(f"有效B2B客户数: {len(valid_rows)}家")

# 按行业统计
by_industry = {}
for r in valid_rows:
    ind = r[0]
    if ind not in by_industry:
        by_industry[ind] = []
    by_industry[ind].append(r)

print("\n分行业有效客户数:")
sorted_industries = sorted(by_industry.items(), key=lambda x: -len(x[1]))
for ind, customers in sorted_industries:
    print(f"  {ind}: {len(customers)}家")

# 生成7天清单（每天100组）
days = ['周一_0922', '周二_0923', '周三_0924', '周四_0925', '周五_0926', '周六_0927', '周日_0928']
daily_lists = {day: [] for day in days}

# 先分配GEO重点行业（均衡分配到7天）
geo_industries = ['医疗器械', '机械装备汽配', '新材料化工', '环保检测', '检验检测', '智能制造', '自动化设备', '模具', '数控机床', '精密机械', '新能源充电电力', '液压设备']
geo_customers = []
for ind in geo_industries:
    if ind in by_industry:
        geo_customers.extend(by_industry[ind])

random.shuffle(geo_customers)
for i, c in enumerate(geo_customers):
    day_idx = i % 7
    day = days[day_idx]
    daily_lists[day].append(c)

# 再分配其他行业客户（补充到每天100组）
other_customers = []
for ind, customers in by_industry.items():
    if ind not in geo_industries:
        other_customers.extend(customers)

random.shuffle(other_customers)
for c in other_customers:
    available_days = [day for day, slots in [(d, 100 - len(daily_lists[d])) for d in days] if slots > 0]
    if not available_days:
        break
    day = random.choice(available_days)
    daily_lists[day].append(c)

# 保存为CSV
for day, customers in daily_lists.items():
    output_path = os.path.join(output_dir, f'有效B2B客户_{day}.csv')
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['行业', '企业名称', '电话', '地址', '备注'])
        writer.writerows([[c[0], c[1], c[2], c[3], c[4]] for c in customers])
    print(f"\n{day}: {len(customers)}家（GEO行业{sum(1 for c in customers if c[0] in geo_industries)}家）")

print(f"\n已保存到: {output_dir}")

conn.close()
