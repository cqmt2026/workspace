# -*- coding: utf-8 -*-
"""重新筛选有效B2B客户（1000组）"""
import sqlite3
import csv

db_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
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
        if kw in name:
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
for ind, customers in sorted_industries:
    print(f"  {ind}: {len(customers)}家")

# 保存为CSV
output_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets\有效B2B客户_最终版.csv'
with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['行业', '企业名称', '电话', '地址', '备注'])
    for r in valid_rows:
        writer.writerow([r[0], r[1], r[2], r[3], r[4] or ''])

print(f"\n已保存到: {output_path}")

conn.close()
