import sqlite3
conn = sqlite3.connect('C:/Users/Administrator/.openclaw/workspace/workspace-baiduagent/data/baidu_crm.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 查询Top10未联系/需跟进的客户，按行业优先级
cur.execute("""SELECT id, name, industry, tier, phone, status, last_call FROM customers 
    WHERE tier='A' AND status IN ('待联系','需跟进') AND phone IS NOT NULL AND phone != ''
    ORDER BY 
      CASE industry 
        WHEN '医疗器械' THEN 1
        WHEN '新材料化工' THEN 2
        WHEN '机械装备汽配' THEN 3
        WHEN '环保检测' THEN 4
        WHEN '建筑建材' THEN 5
        WHEN '新能源充电电力' THEN 6
        ELSE 7
      END,
      last_call ASC
    LIMIT 10""")
rows = cur.fetchall()

for r in rows:
    print(f"ID:{r['id']}|NAME:{r['name']}|IND:{r['industry']}|PHONE:{r['phone']}|STATUS:{r['status']}|LAST:{r['last_call']}")

conn.close()
