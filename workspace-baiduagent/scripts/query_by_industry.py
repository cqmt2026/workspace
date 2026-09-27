import sqlite3

conn = sqlite3.connect('C:/Users/Administrator/.openclaw/workspace/workspace-baiduagent/data/baidu_crm.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 各行业的有电话客户
industries = ['新材料化工', '机械装备汽配', '环保检测', '新能源充电电力']
for ind in industries:
    cur.execute("SELECT id, name, industry, phone FROM customers WHERE tier='A' AND phone IS NOT NULL AND phone != '' AND industry=? LIMIT 5", (ind,))
    rows = cur.fetchall()
    print(f"\n=== {ind} ({len(rows)} found) ===")
    for r in rows:
        print(f"  ID:{r['id']} | {r['name']} | {r['phone']}")

conn.close()
