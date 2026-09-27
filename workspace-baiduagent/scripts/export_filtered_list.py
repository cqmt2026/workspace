#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出下周三天拨打清单（过滤宠物医院）"""
import sqlite3
import random

DB = 'data/baidu_crm.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

# 获取所有有电话的企业，排除宠物医院
c.execute('''SELECT id, name, industry, phone, district 
             FROM customers 
             WHERE phone IS NOT NULL 
             AND phone != ""
             AND industry != "宠物医院"
             ORDER BY id''')
all_customers = c.fetchall()

print(f'总客户数（排除宠物医院）：{len(all_customers)}家')

# 打乱
random.seed(20260927)
random.shuffle(all_customers)

# 分组
day1 = all_customers[:200]
day2 = all_customers[200:400]
day3 = all_customers[400:600]

print(f'周一：{len(day1)}家')
print(f'周二：{len(day2)}家')
print(f'周三：{len(day3)}家')

# 按行业统计
industry_count = {}
for day_name, day_data in [('周一', day1), ('周二', day2), ('周三', day3)]:
    for cust in day_data:
        industry = cust[2]
        industry_count[industry] = industry_count.get(industry, 0) + 1

print('\n行业分布TOP10:')
for ind, cnt in sorted(industry_count.items(), key=lambda x: -x[1])[:10]:
    print(f'  {ind}: {cnt}家')

# 生成Markdown表格
lines = []
lines.append('# 下周三天拨打清单（已过滤宠物医院）')
lines.append('')
lines.append('> 生成时间：2026-09-27')
lines.append('> 每天200家，共600家，不重复')
lines.append('> 已过滤：宠物医院（上周验证零需求）')
lines.append('')

for day_name, day_data in [('周一 09-29', day1), ('周二 09-30', day2), ('周三 10-01', day3)]:
    lines.append(f'## {day_name}')
    lines.append('')
    lines.append('| 序号 | 企业名称 | 行业 | 电话 | 区域 |')
    lines.append('|------|---------|------|------|------|')
    
    for i, cust in enumerate(day_data, 1):
        idx, name, industry, phone, district = cust
        lines.append(f'| {i} | {name} | {industry} | {phone} | {district} |')
    
    lines.append('')
    lines.append('---')
    lines.append('')

conn.close()

# 写入文件
with open('assets/下周三天拨打清单_20260929-09-30_过滤版.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('\n已导出：assets/下周三天拨打清单_20260929-09-30_过滤版.md')
