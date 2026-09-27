"""生成民营医院/体检中心客户清单（仅人类医疗）"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
import csv
from datetime import datetime

# 连接数据库
conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c = conn.cursor()

print('=== 查询民营医院和体检中心客户（仅人类医疗）===')

# 查询所有医院，排除宠物医院
c.execute("""
    SELECT name, industry, phone, address, district 
    FROM customers 
    WHERE industry LIKE '%医院%' 
    AND phone IS NOT NULL AND phone != ''
    AND district IS NOT NULL
    AND name NOT LIKE '%宠物%' 
    AND name NOT LIKE '%动物%'
    AND industry NOT LIKE '%宠物%'
    AND industry NOT LIKE '%动物%'
    ORDER BY district, name
""")
hospitals = c.fetchall()

# 查询体检中心
c.execute("""
    SELECT name, industry, phone, address, district 
    FROM customers 
    WHERE industry LIKE '%体检%' 
    AND phone IS NOT NULL AND phone != ''
    AND district IS NOT NULL
    ORDER BY district, name
""")
checkups = c.fetchall()

# 查询民营医院
c.execute("""
    SELECT name, industry, phone, address, district 
    FROM customers 
    WHERE industry LIKE '%民营%' 
    AND phone IS NOT NULL AND phone != ''
    AND district IS NOT NULL
    AND name NOT LIKE '%宠物%' 
    AND name NOT LIKE '%动物%'
    AND industry NOT LIKE '%宠物%'
    AND industry NOT LIKE '%动物%'
    ORDER BY district, name
""")
private_hospitals = c.fetchall()

print(f'医院（人类医疗）: {len(hospitals)}家')
print(f'体检中心: {len(checkups)}家')
print(f'民营医院: {len(private_hospitals)}家')

# 去重合并
all_hospitals = list(set(hospitals))  # 去重
all_checkups = list(set(checkups))

# 按区县统计
print('\n=== 按区县分布（医院） ===')
district_stats = {}
for row in all_hospitals:
    district = row[4] if row[4] else '未知'
    if district not in district_stats:
        district_stats[district] = 0
    district_stats[district] += 1

for district, count in sorted(district_stats.items(), key=lambda x: -x[1]):
    print(f'{district}: {count}家')

# 生成清单文件
output_file = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\民营医院体检中心客户清单_人类医疗.csv'
with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['序号', '客户名称', '行业类型', '电话', '地址', '区县', '客户类型', '美团上线状态'])
    
    for i, row in enumerate(all_hospitals, 1):
        # 判断是否民营
        is_private = '民营' in row[1] if row[1] else False
        client_type = '民营医院' if is_private else '医院'
        writer.writerow([i, row[0], row[1], row[2], row[3], row[4], client_type, '待核实'])
    
    for i, row in enumerate(all_checkups, len(all_hospitals) + 1):
        writer.writerow([i, row[0], row[1], row[2], row[3], row[4], '体检中心', '待核实'])

print(f'\n清单已生成: {output_file}')
print(f'总计: {len(all_hospitals) + len(all_checkups)}家')

# 显示前30条
print('\n=== 前30条客户示例 ===')
all_clients = all_hospitals + all_checkups
for i, row in enumerate(all_clients[:30], 1):
    is_private = '民营' in row[1] if row[1] else False
    client_type = '民营医院' if is_private else '医院'
    print(f'{i}. {row[0]} | {client_type} | {row[2]} | {row[4]}')

conn.close()
