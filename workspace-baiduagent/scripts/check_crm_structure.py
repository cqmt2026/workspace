# -*- coding: utf-8 -*-
"""检查CRM当前完整状态，为表结构修复做准备"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=" * 70)
print("【CRM数据库 - 修复前检查】")
print("=" * 70)

# 1. 当前表结构
print("\n📋 当前customers表结构:")
cur.execute("PRAGMA table_info(customers)")
cols = cur.fetchall()
for c in cols:
    print(f"   {c[0]}: {c[1]} ({c[2]})")

# 2. 数据量
cur.execute("SELECT COUNT(*) FROM customers")
total = cur.fetchone()[0]
print(f"\n📊 总客户: {total:,}家")

# 3. 现有数据字段填充情况
print("\n📊 各字段填充情况:")
for field in ['name', 'industry', 'tier', 'phone', 'contact', 'source', 'status', 'note']:
    cur.execute(f"SELECT COUNT(*) FROM customers WHERE {field} IS NOT NULL AND {field} != ''")
    cnt = cur.fetchone()[0]
    print(f"   {field}: {cnt}家 ({cnt*100//total if total else 0}%)")

# 4. note字段里的信息（是否含地址/区域）
print("\n📊 note字段示例（含地址/区域信息）:")
cur.execute("SELECT name, note FROM customers WHERE note IS NOT NULL AND note != '' LIMIT 5")
for r in cur.fetchall():
    print(f"   {r[0][:20]}...: {r[1][:50]}...")

# 5. 其他表
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("\n📋 所有表:")
for r in cur.fetchall():
    print(f"   {r[0]}")

conn.close()
