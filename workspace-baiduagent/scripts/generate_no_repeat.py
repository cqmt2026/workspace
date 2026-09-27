# -*- coding: utf-8 -*-
"""生成7天不重复客户清单（每天100组）"""
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
    SELECT id, industry, name, phone, address, note 
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
    customer_id = r[0]
    name = str(r[2])
    industry = r[1]
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
    ind = r[1]
    if ind not in by_industry:
        by_industry[ind] = 0
    by_industry[ind] += 1

print("\n分行业有效客户数:")
sorted_industries = sorted(by_industry.items(), key=lambda x: -x[1])
for ind, count in sorted_industries[:20]:
    print(f"  {ind}: {count}家")

# 定义日期
days = ['周一_0922', '周二_0923', '周三_0924', '周四_0925', '周五_0926', '周六_0927', '周日_0928']

# 洗牌并分配（确保不重复）
random.shuffle(valid_rows)

# 分配7天，每天100组
all_days_customers = []
current_idx = 0

for day in days:
    day_customers = valid_rows[current_idx:current_idx+100]
    current_idx += 100
    all_days_customers.append((day, day_customers))
    
    # 按行业统计
    by_ind_day = {}
    for r in day_customers:
        ind = r[1]
        by_ind_day[ind] = by_ind_day.get(ind, 0) + 1
    
    print(f"\n{day}: {len(day_customers)}组（不重复）")
    for ind, count in sorted(by_ind_day.items(), key=lambda x: -x[1])[:10]:
        print(f"  {ind}: {count}组")

# 保存为CSV（确保不重复）
for day, day_customers in all_days_customers:
    output_path = os.path.join(output_dir, f'有效客户_{day}.csv')
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['id', '行业', '企业名称', '电话', '地址', '备注'])
        for r in day_customers:
            writer.writerow([r[0], r[1], r[2], r[3], r[4], r[5] or ''])
    
    print(f"已保存: {output_path}")

# 验证不重复
all_ids = set()
for day, day_customers in all_days_customers:
    for r in day_customers:
        all_ids.add(r[0])

print(f"\n验证：总客户数={len(all_ids)}，预期=700，重复={700-len(all_ids)}")

print(f"\n已保存到: {output_dir}")

conn.close()
