# -*- coding: utf-8 -*-
import sqlite3, os
from datetime import date

db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'baidu_crm.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 统计
total = cur.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
tier_a = cur.execute('SELECT COUNT(*) FROM customers WHERE tier="A"').fetchone()[0]
tier_b = cur.execute('SELECT COUNT(*) FROM customers WHERE tier="B"').fetchone()[0]
pending = cur.execute('SELECT COUNT(*) FROM customers WHERE status="待联系"').fetchone()[0]
print(f"总客户: {total}, A类: {tier_a}, B类: {tier_b}, 待联系: {pending}")

# Top20客户
cur.execute('SELECT id, name, industry, tier, phone, status FROM customers ORDER BY CASE tier WHEN "A" THEN 1 WHEN "B" THEN 2 ELSE 3 END, id DESC LIMIT 20')
rows = cur.fetchall()
for r in rows:
    print(f"#{r[0]} [{r[3]}] {r[1]} | {r[2]} | {r[4]} | {r[5]}")

conn.close()
