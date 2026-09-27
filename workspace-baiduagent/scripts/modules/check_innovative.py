import sqlite3
db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%'")
print(f'创新型总数: {c.fetchone()[0]}')
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%' AND phone IS NOT NULL AND phone != ''")
print(f'有电话: {c.fetchone()[0]}')
c.execute("SELECT source, COUNT(*) FROM customers WHERE industry LIKE '%创新型%' GROUP BY source ORDER BY COUNT(*) DESC")
print('\n来源分布:')
for s, n in c.fetchall():
    print(f'  {s}: {n}')
conn.close()