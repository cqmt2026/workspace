#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成今日拨打清单 - 优先高价值行业"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/baidu_crm.db'

# 高价值行业优先级（按客单价和转化潜力）
HIGH_VALUE_INDUSTRIES = [
    ('口腔诊所', 50),      # 高客单价，决策快
    ('医美机构', 30),       # 高客单价
    ('宠物医院', 20),       # 决策链短
    ('医疗器械', 20),       # B2B，精准获客
    ('装修装饰', 20),       # 本地服务
    ('教培机构', 20),       # 季节性需求
    ('机械装备汽配', 15),   # B2B，专精特新多
    ('酒店餐饮', 15),       # 本地生活
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

print("="*60)
print("【今日拨打清单】2026-08-30")
print("="*60)

total_list = []
for industry, limit in HIGH_VALUE_INDUSTRIES:
    cur.execute("""
        SELECT id, name, phone, address, district, industry, source
        FROM customers 
        WHERE industry = ? AND phone IS NOT NULL AND phone != '' AND status = '待联系'
        ORDER BY RANDOM()
        LIMIT ?
    """, (industry, limit))
    rows = cur.fetchall()
    for r in rows:
        total_list.append({
            'id': r[0],
            'name': r[1],
            'phone': r[2],
            'address': r[3],
            'district': r[4],
            'industry': r[5],
            'source': r[6],
        })

conn.close()

print(f"\n清单共 {len(total_list)} 条客户\n")
print(f"{'序号':<4} {'行业':<10} {'企业':<30} {'电话':<15} {'区域':<8}")
print("-"*80)
for i, c in enumerate(total_list, 1):
    name = c['name'][:28] if len(c['name']) > 28 else c['name']
    phone = c['phone'][:12] if c['phone'] else '无'
    print(f"{i:<4} {c['industry']:<10} {name:<30} {phone:<15} {c['district'] or '-':<8}")

# 按行业分组统计
from collections import Counter
ind_count = Counter(c['industry'] for c in total_list)
print(f"\n{'='*60}")
print("行业分布:")
for ind, cnt in ind_count.most_common():
    print(f"  {ind}: {cnt}家")
