import sqlite3
conn=sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c=conn.cursor()

# 检查经信委来源的样本有没有被更新
c.execute("SELECT id, name, phone FROM customers WHERE source LIKE '%经信委%' AND industry='创新型中小企业' LIMIT 10")
print("经信委样本:")
for r in c.fetchall():
    print(f"  id={r[0]} name='{r[1][:30]}' phone={r[2]}")

# 检查所有有电话的创新型中小企业
c.execute("SELECT id, name, phone, source FROM customers WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!='' ORDER BY id")
print("\n创新型中小企业有电话的:")
for r in c.fetchall():
    print(f"  id={r[0]} name='{r[1][:35]}' phone={r[2]} source={r[3]}")

conn.close()
