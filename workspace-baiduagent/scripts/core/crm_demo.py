# -*- coding: utf-8 -*-
"""CRM效果展示"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()

# 数据表结构
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("📊 CRM 数据库结构:", tables)

# 各表数据量
for t in ['customers', 'call_logs', 'industry_cards']:
    if t in tables:
        c.execute(f'SELECT COUNT(*) FROM {t}')
        print(f"  {t}: {c.fetchone()[0]} 条")

print("\n" + "="*50)
print("💼 客户表 (customers) 样例")
print("="*50)
c.execute("SELECT id, name, industry, tier, phone, source, status FROM customers ORDER BY id LIMIT 8")
for r in c.fetchall():
    print(f"  [{r[0]}] {r[1]} | {r[2]} | {r[3]}级 | {r[4]} | {r[5]} | {r[6]}")

print("\n" + "="*50)
print("🏭 分行业客户统计")
print("="*50)
c.execute("SELECT industry, COUNT(*) FROM customers GROUP BY industry ORDER BY COUNT(*) DESC")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}家")

print("\n" + "="*50)
print("📞 通话记录表 (call_logs) 结构")
print("="*50)
c.execute("PRAGMA table_info(call_logs)")
cols = [r[1] for r in c.fetchall()]
print("  字段:", cols)

print("\n" + "="*50)
print("📈 行业数据卡表 (industry_cards) 结构")
print("="*50)
c.execute("PRAGMA table_info(industry_cards)")
cols = [r[1] for r in c.fetchall()]
print("  字段:", cols)

conn.close()