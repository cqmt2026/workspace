import sqlite3
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()
cur.execute("SELECT industry, COUNT(*) FROM customers WHERE tier='A' GROUP BY industry ORDER BY COUNT(*) DESC")
for r in cur.fetchall():
    print(r)
print("---")
cur.execute("SELECT id, name, industry, phone FROM customers WHERE tier='A' AND status='待联系' ORDER BY id LIMIT 20")
for r in cur.fetchall():
    print(r)
conn.close()
