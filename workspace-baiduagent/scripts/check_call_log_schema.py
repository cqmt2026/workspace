#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查通话记录表结构并完善"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/baidu_crm.db'

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 检查call_logs表结构
print("=== call_logs表当前结构 ===")
cur.execute("PRAGMA table_info(call_logs)")
columns = cur.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]}) {'NOT NULL' if col[3] else ''}")

# 检查是否有数据
cur.execute("SELECT COUNT(*) FROM call_logs")
count = cur.fetchone()[0]
print(f"\n当前通话记录数: {count}")

# 建议完善字段
print("\n=== 建议完善的字段 ===")
suggested_fields = {
    'customer_id': 'INTEGER - 客户ID关联',
    'call_date': 'TEXT - 拨打日期',
    'duration_sec': 'INTEGER - 通话时长(秒)',
    'result': 'TEXT - 结果(接通/未接通/有意向/无意向/需跟进)',
    'pain_point': 'TEXT - 痛点记录',
    'current_channel': 'TEXT - 当前获客渠道',
    'budget_range': 'TEXT - 预算量级',
    'decision_maker': 'TEXT - 决策人',
    'next_action': 'TEXT - 下一步行动',
    'script_version': 'TEXT - 使用话术版本',
    'note': 'TEXT - 备注',
}

for field, desc in suggested_fields.items():
    existing = [c[1] for c in columns]
    status = '✓ 已有' if field in existing else '✗ 缺失'
    print(f"  {status} {field}: {desc}")

# 检查customers表是否有last_call字段
print("\n=== customers表拨打相关字段 ===")
cur.execute("PRAGMA table_info(customers)")
cust_cols = [c[1] for c in cur.fetchall()]
call_related = [c for c in cust_cols if 'call' in c.lower() or 'last' in c.lower()]
print(f"  拨打相关字段: {call_related}")

conn.close()
