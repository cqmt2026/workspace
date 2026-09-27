# -*- coding: utf-8 -*-
"""筛选有效客户（B2C也适合GEO，但要有规模）"""
import sqlite3
import csv
import os
import re
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
print(f"A类有电话客户总数: {len(all_rows)}家")

# 关键词过滤 - 保留有规模的企业
keywords_remove = [
    # 排除门市/小店/个体户
    '经营部', '商店', '小店', '铺', '摊位', '档口',
    '零售', '批发', '经销', '代销',
    # 排除个人工作室
    '工作室', '个人', '兼职',
    # 排除超小规模
    '维修点', '服务中心', '网点',
]

keywords_keep = [
    '有限公司', '集团', '股份', '总厂', '分厂', '制造', '生产', '实业', '工贸', 
    '科技', '技术', '设备', '机械', '汽车', '电子', '化工', '新材料', '环保', 
    '检测', '能源', '电力', '建设', '工程', '建筑', '建材', '材料', '精密', 
    '自动化', '智能', '新能源', '商贸', '贸易', '物流', '运输', '仓储',
    # 大型连锁/品牌
    '连锁', '品牌', '旗舰店', '总部', '分公司', '子公司',
    # 服务型企业（有规模）
    '医院', '诊所', '口腔', '牙科', '眼科', '美容', '整形', '医美',
    '培训', '教育', '学校', '学院', '驾校', '托管',
    '家政', '保洁', '物业', '安保', '物流', '快递',
    '广告', '传媒', '设计', '咨询', '法律', '会计', '财税',
    '酒店', '餐饮', '美食', '酒楼', '饭店', '餐厅',
    '健身', '瑜伽', '体育', '游泳', '攀岩',
    '摄影', '照相', '婚庆', '婚礼',
]

valid_rows = []
for r in all_rows:
    name = str(r[1])
    industry = r[0]
    combined = name + ' ' + industry
    
    # 排除词
    skip = False
    for kw in keywords_remove:
        if kw in combined:
            skip = True
            break
    if skip:
        continue
    
    # 必须包含关键词
    keep = False
    for kw in keywords_keep:
        if kw in combined:
            keep = True
            break
    if not keep:
        continue
    
    valid_rows.append(r)

print(f"筛选后有效客户数: {len(valid_rows)}家")

# 按行业统计
by_industry = {}
for r in valid_rows:
    ind = r[0]
    if ind not in by_industry:
        by_industry[ind] = []
    by_industry[ind].append(r)

print("\n分行业有效客户数:")
sorted_industries = sorted(by_industry.items(), key=lambda x: -len(x[1]))
for ind, customers in sorted_industries[:40]:
    print(f"  {ind}: {len(customers)}家")

# 生成7天清单（每天100组）
days = ['周一_0922', '周二_0923', '周三_0924', '周四_0925', '周五_0926', '周六_0927', '周日_0928']
daily_lists = {day: [] for day in days}

# 先分配GEO重点行业（均衡分配到7天）
geo_industries = ['医疗器械', '机械装备汽配', '新材料化工', '环保检测', '检验检测', '智能制造', '自动化设备', '模具', '数控机床', '精密机械', '新能源充电电力', '液压设备', '装修装饰', '教培机构', '房产中介']
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
    output_path = os.path.join(output_dir, f'有效客户_{day}.csv')
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['行业', '企业名称', '电话', '地址', '备注'])
        writer.writerows([[c[0], c[1], c[2], c[3], c[4]] for c in customers])
    print(f"\n{day}: {len(customers)}家（GEO行业{sum(1 for c in customers if c[0] in geo_industries)}家）")

print(f"\n已保存到: {output_dir}")

conn.close()
