import sqlite3
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()
# Check what industries have phone numbers in 医疗器械
cur.execute("SELECT id, name, industry, phone FROM customers WHERE industry='医疗器械' AND tier='A' AND phone != '' ORDER BY id LIMIT 15")
for r in cur.fetchall():
    print(r)
print("---")
# Check 新材料化工
cur.execute("SELECT id, name, industry, phone FROM customers WHERE industry='新材料化工' AND tier='A' AND phone != '' ORDER BY id LIMIT 10")
for r in cur.fetchall():
    print(r)
print("---")
# Check 机械装备汽配
cur.execute("SELECT id, name, industry, phone FROM customers WHERE industry='机械装备汽配' AND tier='A' AND phone != '' ORDER BY id LIMIT 10")
for r in cur.fetchall():
    print(r)
conn.close()
