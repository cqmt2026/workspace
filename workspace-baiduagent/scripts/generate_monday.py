# -*- coding: utf-8 -*-
"""生成周一100组有效客户"""
import sqlite3
import csv
import random

db_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
output_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets\有效客户_周一_0922.csv'

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

# 关键词过滤
keywords_remove = [
    '经营部', '商店', '小店', '铺', '摊位', '档口',
    '零售', '批发', '经销', '代销',
    '工作室', '个人', '兼职',
    '维修点', '服务中心', '网点',
]

keywords_keep = [
    '有限公司', '集团', '股份', '总厂', '分厂', '制造', '生产', '实业', '工贸', 
    '科技', '技术', '设备', '机械', '汽车', '电子', '化工', '新材料', '环保', 
    '检测', '能源', '电力', '建设', '工程', '建筑', '建材', '材料', '精密', 
    '自动化', '智能', '新能源', '商贸', '贸易', '物流', '运输', '仓储',
    '连锁', '品牌', '旗舰店', '总部', '分公司', '子公司',
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
    
    skip = False
    for kw in keywords_remove:
        if kw in combined:
            skip = True
            break
    if skip:
        continue
    
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
for ind, customers in sorted_industries[:20]:
    print(f"  {ind}: {len(customers)}家")

# 随机抽取100组
random.shuffle(valid_rows)
monday_rows = valid_rows[:100]

# 保存为CSV
with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['行业', '企业名称', '电话', '地址', '备注'])
    for r in monday_rows:
        writer.writerow([r[0], r[1], r[2], r[3], r[4] or ''])

print(f"\n已保存到: {output_path}")
print(f"周一客户数: {len(monday_rows)}组")

# 按行业统计周一客户
by_industry_mon = {}
for r in monday_rows:
    ind = r[0]
    by_industry_mon[ind] = by_industry_mon.get(ind, 0) + 1

print("\n周一分行业客户数:")
for ind, count in sorted(by_industry_mon.items(), key=lambda x: -x[1]):
    print(f"  {ind}: {count}组")

conn.close()
