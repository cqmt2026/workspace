#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出下周三天拨打清单，每天200家，不重复"""
import sqlite3
import random

DB = 'data/baidu_crm.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

# 获取所有有电话的企业
c.execute('''SELECT id, name, industry, phone, district 
             FROM customers 
             WHERE phone IS NOT NULL 
             AND phone != ""
             ORDER BY id''')
all_customers = c.fetchall()
print(f'总客户数：{len(all_customers)}家')
print(f'有电话客户数：{len(all_customers)}家')

# 打乱顺序
random.seed(20260927)
random.shuffle(all_customers)

# 分三天，每天200家
day1 = all_customers[:200]
day2 = all_customers[200:400]
day3 = all_customers[400:600]

print(f'\n周一：{len(day1)}家')
print(f'周二：{len(day2)}家')
print(f'周三：{len(day3)}家')

# 导出到文件
with open('assets/下周三天拨打清单_20260929-09-30.md', 'w', encoding='utf-8') as f:
    f.write('# 下周三天拨打清单\n\n')
    f.write('> 生成时间：2026-09-27\n')
    f.write('> 每天200家，共600家，不重复\n\n')
    
    for day_name, day_data in [('周一 09-29', day1), ('周二 09-30', day2), ('周三 10-01', day3)]:
        f.write(f'## {day_name}\n\n')
        f.write('| 序号 | 企业名称 | 行业 | 电话 | 区域 |\n')
        f.write('|------|---------|------|------|------|\n')
        
        # 按行业分组统计
        industry_count = {}
        for i, cust in enumerate(day_data, 1):
            idx, name, industry, phone, district = cust
            industry_count[industry] = industry_count.get(industry, 0) + 1
            f.write(f'| {i} | {name} | {industry} | {phone} | {district} |\n')
        
        f.write(f'\n**行业分布：**\n')
        for ind, cnt in sorted(industry_count.items(), key=lambda x: -x[1])[:10]:
            f.write(f'- {ind}：{cnt}家\n')
        f.write('\n---\n\n')

conn.close()
print('\n已导出：assets/下周三天拨打清单_20260929-09-30.md')
