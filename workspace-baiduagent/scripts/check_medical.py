import sqlite3
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()
# Check what industries map to '医疗器械' - seems like too broad
cur.execute("SELECT industry, COUNT(*) FROM customers WHERE industry LIKE '%医疗%' AND tier='A' GROUP BY industry ORDER BY COUNT(*) DESC")
for r in cur.fetchall():
    print(r)
conn.close()
