import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c = conn.cursor()

print("=== Tables ===")
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
for r in c.fetchall(): print(f"  {r[0]}")

print("\n=== Customer Stats ===")
c.execute("SELECT COUNT(*) FROM customers")
total = c.fetchone()[0]
print(f"Total: {total}")

c.execute("SELECT COUNT(*) FROM call_logs")
print(f"Call logs: {c.fetchone()[0]}")

c.execute("SELECT COUNT(DISTINCT phone) FROM customers WHERE phone IS NOT NULL AND phone != ''")
with_phone = c.fetchone()[0]
print(f"With phone: {with_phone} ({with_phone/total*100:.1f}%)")

c.execute("SELECT COUNT(*) FROM customers WHERE district IS NULL OR district = ''")
no_district = c.fetchone()[0]
print(f"No district: {no_district}")

c.execute("SELECT COUNT(*) FROM customers WHERE tier IS NULL OR tier = ''")
no_tier = c.fetchone()[0]
print(f"No tier: {no_tier}")

print("\n=== Status Distribution ===")
c.execute("SELECT status, COUNT(*) FROM customers GROUP BY status")
for r in c.fetchall(): print(f"  {r[0]}: {r[1]}")

print("\n=== Tier Distribution ===")
c.execute("SELECT tier, COUNT(*) FROM customers GROUP BY tier")
for r in c.fetchall(): print(f"  {r[0] or '(null)'}: {r[1]}")

print("\n=== Top 15 Industries by Phone Coverage ===")
c.execute("""
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as with_phone
    FROM customers
    GROUP BY industry
    ORDER BY with_phone DESC
    LIMIT 15
""")
for r in c.fetchall():
    pct = r[2]/r[1]*100 if r[1] > 0 else 0
    print(f"  {r[0]}: {r[2]}/{r[1]} ({pct:.1f}%)")

print("\n=== Bottom 10 Industries by Phone Coverage ===")
c.execute("""
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as with_phone
    FROM customers
    GROUP BY industry
    HAVING total >= 10
    ORDER BY pct ASC
    LIMIT 10
""")
# need to recalculate
c.execute("""
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as with_phone,
           ROUND(CAST(SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 1) as pct
    FROM customers
    GROUP BY industry
    HAVING total >= 10
    ORDER BY pct ASC
    LIMIT 10
""")
for r in c.fetchall():
    print(f"  {r[0]}: {r[2]}/{r[1]} ({r[3]}%)")

print("\n=== Source Distribution (Top 15) ===")
c.execute("""
    SELECT data_source, COUNT(*) as cnt
    FROM customers
    GROUP BY data_source
    ORDER BY cnt DESC
    LIMIT 15
""")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n=== Phone Format Issues ===")
c.execute("""
    SELECT COUNT(*) FROM customers
    WHERE phone IS NOT NULL AND phone != ''
    AND LENGTH(phone) < 7
""")
short_phones = c.fetchone()[0]
print(f"Short phones (<7 digits): {short_phones}")

c.execute("""
    SELECT COUNT(*) FROM customers
    WHERE phone IS NOT NULL AND phone != ''
    AND (phone GLOB '*[^0-9]*' OR phone GLOB '* *' OR phone GLOB '*-*')
""")
dirty_phones = c.fetchone()[0]
print(f"Dirty format phones: {dirty_phones}")

conn.close()
print("\nDone!")
