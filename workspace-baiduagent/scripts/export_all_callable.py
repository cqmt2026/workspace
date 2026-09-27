#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出所有有电话的企业清单（按行业分组）"""
import sqlite3
from collections import defaultdict

DB = 'data/baidu_crm.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

# 按行业统计有电话数量
c.execute('''SELECT industry, 
             COUNT(*) as total,
             SUM(CASE WHEN phone IS NOT NULL AND phone != "" THEN 1 ELSE 0 END) as has_phone
             FROM customers 
             GROUP BY industry 
             ORDER BY has_phone DESC''')
rows = c.fetchall()

print('=' * 60)
print('各行业有电话企业统计')
print('=' * 60)

industry_stats = []
for r in rows:
    if r[2] > 0:  # 只打印有电话的
        industry_stats.append({
            'industry': r[0],
            'total': r[1],
            'has_phone': r[2],
            'coverage': r[2] / r[1] * 100 if r[1] > 0 else 0
        })
        print(f'{r[0]}: {r[2]}/{r[1]}家 ({r[2]/r[1]*100:.1f}%)')

# 导出Top50到文件
print('\n导出Top50可拨打清单...')
with open('assets/今日可拨打清单_Top50.md', 'w', encoding='utf-8') as f:
    f.write('# 今日可拨打清单 Top50\n\n')
    f.write(f'> 生成时间：2026-09-27\n')
    f.write(f'> 总计：{len(industry_stats)}个行业有电话\n\n')
    f.write('| 序号 | 行业 | 企业名称 | 电话 | 覆盖率 |\n')
    f.write('|------|------|---------|------|--------|\n')
    
    for i, s in enumerate(industry_stats[:50], 1):
        f.write(f'| {i} | {s["industry"]} | - | {s["has_phone"]}家 | {s["coverage"]:.1f}% |\n')

conn.close()
print('✅ 已导出：assets/今日可拨打清单_Top50.md')
