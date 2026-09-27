import sqlite3
conn = sqlite3.connect('C:/Users/Administrator/.openclaw/workspace/workspace-baiduagent/data/baidu_crm.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. 客户统计
cur.execute("SELECT COUNT(*) FROM customers WHERE tier='A'")
print("A类总数:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM customers WHERE tier='A' AND status='待联系'")
print("待联系A类:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM customers WHERE tier='A' AND status='需跟进'")
print("需跟进A类:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM customers WHERE tier='A' AND status='已联系'")
print("已联系A类:", cur.fetchone()[0])

# 2. 行业分布
cur.execute("SELECT industry, COUNT(*) as cnt FROM customers WHERE tier='A' GROUP BY industry ORDER BY cnt DESC")
print("\n行业分布:")
for r in cur.fetchall():
    print(f"  {r['industry']}: {r['cnt']}")

# 3. 有电话的待联系客户（按行业优先级）
cur.execute("""SELECT id, name, industry, tier, phone, status, last_call FROM customers 
    WHERE tier='A' AND status IN ('待联系','需跟进') AND phone IS NOT NULL AND phone != ''
    ORDER BY 
      CASE industry 
        WHEN '医疗器械' THEN 1
        WHEN '新材料' THEN 2
        WHEN '机械装备' THEN 3
        WHEN '环保检测' THEN 4
        WHEN '建筑建材' THEN 5
        WHEN '新能源充电' THEN 6
        ELSE 7
      END,
      last_call ASC
    LIMIT 15""")
rows = cur.fetchall()
print("\n有电话的Top客户:")
for r in rows:
    print(f"  {r['id']}|{r['name']}|{r['industry']}|{r['phone']}|{r['status']}|{r['last_call']}")

# 4. 通话记录
cur.execute("""SELECT cl.id, c.name, c.industry, cl.result, cl.call_date FROM call_logs cl 
    JOIN customers c ON cl.customer_id=c.id ORDER BY cl.call_date DESC LIMIT 10""")
print("\n最近通话记录:")
for r in cur.fetchall():
    print(f"  {r['call_date']}|{r['name']}|{r['industry']}|{r['result']}")

conn.close()
