import sqlite3
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()

# call_logs结构
cur.execute("PRAGMA table_info(call_logs)")
cols = cur.fetchall()
print('call_logs columns:')
for c in cols:
    print(f'  {c[1]} ({c[2]})')

# customers结构
cur.execute("PRAGMA table_info(customers)")
cols = cur.fetchall()
print('\ncustomers columns:')
for c in cols:
    print(f'  {c[1]} ({c[2]})')

# call_logs数据量
cur.execute('SELECT COUNT(*) FROM call_logs')
print('\ncall_logs count:', cur.fetchone()[0])

# customers数据量
cur.execute('SELECT COUNT(*) FROM customers')
print('customers count:', cur.fetchone()[0])

# 本周call_logs (8/24-8/30)
cur.execute("SELECT * FROM call_logs WHERE call_date >= '2026-08-24' AND call_date <= '2026-08-30'")
calls = cur.fetchall()
print(f'\n本周通话记录: {len(calls)} 条')
for row in calls:
    print(f'  {row}')

# 查看call_logs样本
cur.execute("SELECT * FROM call_logs LIMIT 5")
print('\ncall_logs sample:')
for row in cur.fetchall():
    print(f'  {row}')

# 本周客户状态分布
cur.execute("SELECT status, COUNT(*) FROM customers GROUP BY status")
print('\ncustomer status distribution:')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

# 本月新增客户
cur.execute("SELECT COUNT(*) FROM customers WHERE date(created_at) >= '2026-08-01'")
print('\n本月新增客户:', cur.fetchone()[0])

# 本月成交客户
cur.execute("SELECT id, name, industry, status FROM customers WHERE status='converted' AND date(created_at)>=date('2026-08-01')")
converted = cur.fetchall()
print(f'\n本月成交客户: {len(converted)} 家')
for row in converted:
    print(f'  {row}')

conn.close()
