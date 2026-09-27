import sqlite3
conn=sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c=conn.cursor()

print("=== 今日创新型中小企业补抓结果汇总 ===")
c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''")
print(f"创新型中小企业有电话: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业'")
print(f"创新型中小企业总数: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业' AND (phone IS NULL OR phone='')")
print(f"创新型中小企业无电话: {c.fetchone()[0]}")

print("\n=== 有电话的创新型中小企业按区域分布 ===")
c.execute("""
    SELECT district, COUNT(*) as cnt
    FROM customers
    WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!='' AND district IS NOT NULL AND district != ''
    GROUP BY district ORDER BY cnt DESC
""")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}家")

print("\n=== 今日新增电话示例（最近更新的） ===")
c.execute("""
    SELECT name, phone, district FROM customers
    WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''
    ORDER BY id DESC LIMIT 15
""")
for r in c.fetchall():
    print(f"  [{r[2] or '未知'}] {r[0][:35]}: {r[1]}")

conn.close()
