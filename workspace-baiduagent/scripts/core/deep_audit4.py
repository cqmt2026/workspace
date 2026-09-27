import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c = conn.cursor()

# 1. Tier distribution check
print("=== Tier Distribution ===")
c.execute("SELECT tier, COUNT(*) FROM customers GROUP BY tier")
for r in c.fetchall():
    print(f"  tier={repr(r[0])}: {r[1]}")

# 2. District coverage by industry (fixed - no district = all industries)
print("\n=== District Coverage by Industry ===")
c.execute("""
    SELECT industry,
           COUNT(*) as total,
           SUM(CASE WHEN district IS NOT NULL AND district != '' THEN 1 ELSE 0 END) as with_district
    FROM customers
    GROUP BY industry
    ORDER BY with_district * 1.0 / total ASC
    LIMIT 15
""")
for r in c.fetchall():
    pct = r[2]/r[1]*100 if r[1] > 0 else 0
    print(f"  {r[0]}: {r[2]}/{r[1]} ({pct:.1f}%)")

# 3. Phone coverage by industry (fixed)
print("\n=== Phone Coverage by Industry ===")
c.execute("""
    SELECT industry,
           COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as with_phone
    FROM customers
    GROUP BY industry
    ORDER BY with_phone * 1.0 / total ASC
    LIMIT 15
""")
for r in c.fetchall():
    pct = r[2]/r[1]*100 if r[1] > 0 else 0
    print(f"  {r[0]}: {r[2]}/{r[1]} ({pct:.1f}%)")

# 4. Check for duplicate names within same industry
print("\n=== Duplicate Names within Same Industry ===")
c.execute("""
    SELECT name, industry, COUNT(*) as cnt
    FROM customers
    GROUP BY name, industry
    HAVING cnt > 1
    LIMIT 10
""")
for r in c.fetchall():
    print(f"  [{r[1]}] {r[0]}: {r[2]} times")

# 5. Check status values
print("\n=== Status Values ===")
c.execute("SELECT status, COUNT(*) FROM customers GROUP BY status")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

# 6. Check call_logs - is it empty?
print("\n=== Call Logs ===")
c.execute("SELECT COUNT(*) FROM call_logs")
print(f"Total call logs: {c.fetchone()[0]}")

# 7. Check the "pending" status customers
print("\n=== Pending Customers ===")
c.execute("SELECT id, name, industry, tier, phone, source FROM customers WHERE status = 'pending' LIMIT 10")
for r in c.fetchall():
    print(f"  id={r[0]}, {r[1]}, {r[2]}, tier={r[3]}, phone={r[4]}, source={r[5]}")

# 8. Phone quality: count of 023 prefix (Chongqing area code)
print("\n=== Phone Area Code Analysis ===")
c.execute("SELECT COUNT(*) FROM customers WHERE phone GLOB '023*'")
print(f"023 (Chongqing): {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM customers WHERE phone GLOB '1[3-9]*'")
print(f"Mobile (1xxx): {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM customers WHERE phone NOT GLOB '023*' AND phone NOT GLOB '1[3-9]*' AND phone IS NOT NULL AND phone != ''")
print(f"Other: {c.fetchone()[0]}")

# 9. Industry name consistency check
print("\n=== Industry Name Issues ===")
c.execute("""
    SELECT DISTINCT industry FROM customers
    WHERE industry LIKE '%Mech%' OR industry LIKE '%mechan%'
       OR industry LIKE '%Mech%' OR industry LIKE '%机械%'
""")
for r in c.fetchall():
    print(f"  {r[0]}")

c.execute("SELECT DISTINCT industry FROM customers WHERE industry LIKE 'Mech%' OR industry LIKE 'New%' OR industry LIKE 'mechanical%'")
for r in c.fetchall():
    print(f"  {r[0]} (English?)")

conn.close()
print("\nDone!")
