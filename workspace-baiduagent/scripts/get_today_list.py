#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成今日拨打清单"""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'baidu_crm.db')

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. 总体统计
cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
print(f'CRM总客户数: {total}')

cur.execute('SELECT COUNT(DISTINCT customer_id) FROM call_logs')
contacted = cur.fetchone()[0]
print(f'已联系客户数: {contacted}')

cur.execute('SELECT MAX(call_date) FROM call_logs')
last_call = cur.fetchone()[0]
print(f'最近通话日期: {last_call}')

# 2. 通话结果分布
cur.execute('SELECT result, COUNT(*) as cnt FROM call_logs GROUP BY result ORDER BY cnt DESC')
print('\n通话结果分布:')
for r in cur.fetchall():
    print(f'  {r[0]}: {r[1]}')

# 3. 最近通话记录
cur.execute("""
    SELECT c.name, c.industry, cl.result, cl.call_date
    FROM call_logs cl
    JOIN customers c ON c.id = cl.customer_id
    ORDER BY cl.call_date DESC
    LIMIT 10
""")
print('\n最近通话记录:')
for r in cur.fetchall():
    print(f'  {r[0]}|{r[1]}|{r[2]}|{r[3]}')

# 4. 获取A类客户名单，按行业优先级排序
industry_order = {
    '医疗器械': 1, '新材料': 2, '机械装备': 3,
    '环保检测': 4, '新能源': 5, '建筑建材': 6
}
cur.execute("""
    SELECT id, name, industry, tier, phone, status, last_call, district
    FROM customers
    WHERE tier = 'A'
    ORDER BY
        CASE
            WHEN industry = '医疗器械' THEN 1
            WHEN industry = '新材料' THEN 2
            WHEN industry = '机械装备' THEN 3
            WHEN industry = '环保检测' THEN 4
            WHEN industry = '新能源' THEN 5
            WHEN industry = '建筑建材' THEN 6
            ELSE 7
        END,
        last_call IS NULL DESC,
        last_call ASC,
        name
    LIMIT 30
""")
a_customers = cur.fetchall()
print(f'\nA类客户总数: {len(a_customers)}')
print('\nA类客户（按行业优先级+最后联系时间排序）:')
for r in a_customers:
    print(f"  {r[0]}|{r[1]}|{r[2]}|{r[3]}|{r[4]}|{r[5]}|{r[6]}|{r[7]}")

# 5. 获取已联系的客户ID列表
cur.execute('SELECT DISTINCT customer_id FROM call_logs')
contacted_ids = {r[0] for r in cur.fetchall()}
print(f'\n已联系客户ID: {contacted_ids}')

# 6. 筛选未联系或需跟进的客户
pending = []
for r in a_customers:
    if r[0] not in contacted_ids:
        pending.append(('未联系', r))
    else:
        # 检查上次通话结果，看是否需要跟进
        cur.execute("""
            SELECT result, call_date FROM call_logs
            WHERE customer_id = ?
            ORDER BY call_date DESC LIMIT 1
        """, (r[0],))
        last_log = cur.fetchone()
        if last_log and last_log[0] in ('有意向', '需跟进'):
            pending.append(('需跟进', r))

print(f'\n待拨打客户（未联系+需跟进）: {len(pending)}')
for status, r in pending:
    print(f"  [{status}] {r[1]}|{r[2]}|{r[4]}|{r[6]}")

conn.close()
