import sqlite3, os, sys
from datetime import datetime, timedelta

db_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

if not os.path.exists(db_path):
    print("DB not found")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Tables:", tables)

for t in tables:
    tn = t[0]
    cur.execute(f"SELECT COUNT(*) FROM [{tn}]")
    cnt = cur.fetchone()[0]
    print(f"  {tn}: {cnt} rows")

# Call logs stats
today = "2026-08-29"
yesterday = "2026-08-28"

# Today
cur.execute(f"SELECT COUNT(*) FROM call_logs WHERE date(call_date) = '{today}'")
today_calls = cur.fetchone()[0]

cur.execute(f"SELECT COUNT(*) FROM call_logs WHERE date(call_date) = '{today}' AND result = '接通'")
today_connected = cur.fetchone()[0]

cur.execute(f"SELECT COUNT(*) FROM call_logs WHERE date(call_date) = '{today}' AND result = '有效'")
today_effective = cur.fetchone()[0]

cur.execute(f"SELECT COUNT(*) FROM call_logs WHERE date(call_date) = '{today}' AND result = '意向'")
today_intention = cur.fetchone()[0]

cur.execute(f"SELECT COUNT(*) FROM call_logs WHERE date(call_date) = '{today}' AND result = '成交'")
today_deal = cur.fetchone()[0]

# Yesterday
cur.execute(f"SELECT COUNT(*) FROM call_logs WHERE date(call_date) = '{yesterday}'")
yesterday_calls = cur.fetchone()[0]

cur.execute(f"SELECT COUNT(*) FROM call_logs WHERE date(call_date) = '{yesterday}' AND result = '接通'")
yesterday_connected = cur.fetchone()[0]

cur.execute(f"SELECT COUNT(*) FROM call_logs WHERE date(call_date) = '{yesterday}' AND result = '有效'")
yesterday_effective = cur.fetchone()[0]

cur.execute(f"SELECT COUNT(*) FROM call_logs WHERE date(call_date) = '{yesterday}' AND result = '意向'")
yesterday_intention = cur.fetchone()[0]

cur.execute(f"SELECT COUNT(*) FROM call_logs WHERE date(call_date) = '{yesterday}' AND result = '成交'")
yesterday_deal = cur.fetchone()[0]

# Calculate rates
today_rate = (today_connected / today_calls * 100) if today_calls > 0 else 0
yesterday_rate = (yesterday_connected / yesterday_calls * 100) if yesterday_calls > 0 else 0

print(f"\n=== Today ({today}) ===")
print(f"拨打数: {today_calls}")
print(f"接通数: {today_connected}")
print(f"有效率: {today_rate:.1f}%")
print(f"意向数: {today_intention}")
print(f"成交数: {today_deal}")

print(f"\n=== Yesterday ({yesterday}) ===")
print(f"拨打数: {yesterday_calls}")
print(f"接通数: {yesterday_connected}")
print(f"有效率: {yesterday_rate:.1f}%")
print(f"意向数: {yesterday_intention}")
print(f"成交数: {yesterday_deal}")

# Recent calls
print("\n=== Recent Calls ===")
cur.execute("SELECT call_date, customer_id, duration_sec, result, note FROM call_logs ORDER BY create_time DESC LIMIT 10")
for row in cur.fetchall():
    print(f"  {row}")

# Customers by tier
print("\n=== Customers by Tier ===")
cur.execute("SELECT tier, COUNT(*) FROM customers GROUP BY tier")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
