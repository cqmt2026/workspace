import sqlite3
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()
cur.execute('SELECT tier, status, COUNT(*) FROM customers GROUP BY tier, status ORDER BY tier, status')
for r in cur.fetchall():
    print(r)
print()
cur.execute('SELECT industry, COUNT(*) as cnt FROM customers WHERE tier="A" GROUP BY industry ORDER BY cnt DESC LIMIT 20')
for r in cur.fetchall():
    print(r)
conn.close()
