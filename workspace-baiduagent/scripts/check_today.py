import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()

# 查看表结构
c.execute("PRAGMA table_info(call_logs)")
print("call_logs schema:")
for row in c.fetchall(): print(f"  {row}")

c.execute("PRAGMA table_info(customers)")
print("\ncustomers schema:")
for row in c.fetchall(): print(f"  {row}")

# 最近通话记录（最近10条）
c.execute("SELECT * FROM call_logs ORDER BY id DESC LIMIT 10")
print("\n最近通话记录:")
cols = [desc[0] for desc in c.description]
print(f"  列: {cols}")
for row in c.fetchall(): print(f"  {row}")

# 总客户统计
c.execute("SELECT COUNT(*) FROM customers")
print(f"\n总客户: {c.fetchone()[0]}")

# 客户状态分布
c.execute("SELECT status, COUNT(*) FROM customers GROUP BY status")
print("客户状态分布:")
for row in c.fetchall(): print(f"  {row[0]}: {row[1]}")

conn.close()
