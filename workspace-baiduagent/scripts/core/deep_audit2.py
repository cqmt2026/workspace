import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c = conn.cursor()

print("=== Customers with no phone ===")
c.execute("""
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as with_phone
    FROM customers
    GROUP BY industry
    HAVING total >= 10
    ORDER BY CAST(SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) ASC
    LIMIT 10
""")
for r in c.fetchall():
    pct = r[2]/r[1]*100 if r[1] > 0 else 0
    print(f"  {r[0]}: {r[2]}/{r[1]} ({pct:.1f}%)")

print("\n=== No-phone customers by industry (top 20) ===")
c.execute("""
    SELECT industry, COUNT(*) as cnt
    FROM customers
    WHERE phone IS NULL OR phone = ''
    GROUP BY industry
    ORDER BY cnt DESC
    LIMIT 20
""")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n=== Empty tier customers ===")
c.execute("""
    SELECT industry, COUNT(*) as cnt
    FROM customers
    WHERE tier IS NULL OR tier = ''
    GROUP BY industry
    ORDER BY cnt DESC
    LIMIT 10
""")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n=== Phone format check ===")
c.execute("""
    SELECT COUNT(*) FROM customers
    WHERE phone IS NOT NULL AND phone != ''
    AND LENGTH(REPLACE(REPLACE(REPLACE(phone, '-', ''), ' ', ''), '(', '')) < 11
""")
invalid = c.fetchone()[0]
print(f"Invalid format (<11 digits): {invalid}")

print("\n=== Data source for no-phone customers ===")
c.execute("""
    SELECT data_source, COUNT(*) as cnt
    FROM customers
    WHERE phone IS NULL OR phone = ''
    GROUP BY data_source
    ORDER BY cnt DESC
    LIMIT 10
""")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n=== Industry cards ===")
c.execute("SELECT COUNT(*) FROM industry_cards")
print(f"Cards: {c.fetchone()[0]}")
c.execute("SELECT * FROM industry_cards LIMIT 5")
for r in c.fetchall():
    print(f"  {r}")

print("\n=== Duplicate check ===")
c.execute("""
    SELECT name, COUNT(*) as cnt FROM customers
    GROUP BY name HAVING cnt > 1
    LIMIT 10
""")
dups = c.fetchall()
print(f"Duplicate names: {len(dups)}")
for r in dups[:5]:
    print(f"  {r[0]}: {r[1]} times")

conn.close()
print("\nDone!")
