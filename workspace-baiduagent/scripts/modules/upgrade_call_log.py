#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完善通话记录表结构"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/baidu_crm.db'

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 检查当前字段
cur.execute("PRAGMA table_info(call_logs)")
existing_cols = [c[1] for c in cur.fetchall()]

# 需要添加的字段
new_fields = [
    ('pain_point', 'TEXT'),
    ('current_channel', 'TEXT'),
    ('budget_range', 'TEXT'),
    ('decision_maker', 'TEXT'),
]

added = 0
for field, ftype in new_fields:
    if field not in existing_cols:
        cur.execute(f"ALTER TABLE call_logs ADD COLUMN {field} {ftype}")
        added += 1
        print(f"  ✓ 添加字段: {field} ({ftype})")
    else:
        print(f"  - 已有字段: {field}")

conn.commit()

# 验证新结构
print("\n=== 完善后的call_logs表结构 ===")
cur.execute("PRAGMA table_info(call_logs)")
for col in cur.fetchall():
    print(f"  {col[1]} ({col[2]})")

conn.close()
print(f"\n共添加{added}个新字段")
