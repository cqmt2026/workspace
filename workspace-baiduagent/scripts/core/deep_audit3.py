import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c = conn.cursor()

# Schema
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='customers'")
print("Customers schema:")
print(c.fetchone()[0])
print()

c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='call_logs'")
print("Call logs schema:")
print(c.fetchone()[0])
print()

# Industry distribution
print("=== Industry Distribution ===")
c.execute("SELECT industry, COUNT(*) as cnt FROM customers GROUP BY industry ORDER BY cnt DESC")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Data source column check - it's 'source' not 'data_source'
print("\n=== Source column for no-phone customers ===")
c.execute("""
    SELECT source, COUNT(*) as cnt
    FROM customers
    WHERE phone IS NULL OR phone = ''
    GROUP BY source
    ORDER BY cnt DESC
    LIMIT 15
""")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

# District coverage by industry
print("\n=== District coverage by industry ===")
c.execute("""
    SELECT industry,
           COUNT(*) as total,
           SUM(CASE WHEN district IS NOT NULL AND district != '' THEN 1 ELSE 0 END) as with_district
    FROM customers
    GROUP BY industry
    ORDER BY CAST(SUM(CASE WHEN district IS NOT NULL AND district != '' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) ASC
    LIMIT 10
""")
for r in c.fetchall():
    pct = r[2]/r[1]*100 if r[1] > 0 else 0
    print(f"  {r[0]}: {r[2]}/{r[1]} ({pct:.1f}%)")

# Phone format analysis
print("\n=== Phone format issues ===")
c.execute("SELECT phone, COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != '' GROUP BY phone HAVING COUNT(*) > 1 LIMIT 5")
print("Duplicate phones:")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]} times")

# Check if 电话字段是数字还是字符串
c.execute("SELECT phone FROM customers WHERE phone IS NOT NULL AND phone != '' LIMIT 5")
print("\nSample phones:")
for r in c.fetchall():
    print(f"  {r[0]} (len={len(r[0])})")

conn.close()
print("\nDone!")
