import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c = conn.cursor()

# 1. All industry names
print("=== All Industry Names ===")
c.execute("SELECT DISTINCT industry FROM customers ORDER BY industry")
for r in c.fetchall():
    print(f"  '{r[0]}'")

# 2. Sample of "pending" status customers to understand why
print("\n=== Pending Customer Samples ===")
c.execute("SELECT id, name, industry, phone, source FROM customers WHERE status = 'pending' LIMIT 20")
for r in c.fetchall():
    print(f"  [{r[0]}] {r[1]}, {r[2]}, phone={r[3]}, source={r[4]}")

# 3. Total counts by source type
print("\n=== Source Type Distribution ===")
c.execute("""
    SELECT 
        CASE 
            WHEN source LIKE '%高德%' THEN '高德'
            WHEN source LIKE '%百度%' OR source LIKE '%Baidu%' THEN '百度'
            WHEN source LIKE '%经信委%' OR source LIKE '%创新型%' THEN '经信委'
            WHEN source LIKE '%卫健委%' THEN '卫健委'
            WHEN source LIKE '%教委%' THEN '教委'
            WHEN source LIKE '%专精特新%' THEN '专精特新'
            WHEN source LIKE '%住建委%' THEN '住建委'
            ELSE '其他'
        END as src_type,
        COUNT(*) as cnt
    FROM customers
    GROUP BY src_type
    ORDER BY cnt DESC
""")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

# 4. Check empty district but has lat/lng
print("\n=== District vs Coordinates ===")
c.execute("SELECT COUNT(*) FROM customers WHERE district IS NULL OR district = '' AND lat IS NOT NULL AND lat != ''")
has_coord_no_district = c.fetchone()[0]
print(f"Has coordinates but no district: {has_coord_no_district}")

c.execute("SELECT COUNT(*) FROM customers WHERE district IS NOT NULL AND district != ''")
has_district = c.fetchone()[0]
print(f"Has district: {has_district}")

# 5. The 8254 high-coverage industries mentioned in ledger
print("\n=== High Coverage Industries ===")
c.execute("""
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as with_phone
    FROM customers
    GROUP BY industry
    HAVING total >= 50
    ORDER BY with_phone * 1.0 / total DESC
""")
for r in c.fetchall():
    pct = r[2]/r[1]*100 if r[1] > 0 else 0
    print(f"  {r[0]}: {r[2]}/{r[1]} ({pct:.1f}%)")

conn.close()
print("\nDone!")
