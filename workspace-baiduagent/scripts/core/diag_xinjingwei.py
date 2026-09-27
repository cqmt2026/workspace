import sqlite3, os

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 看看经信委来源的实际企业名称
c.execute("""SELECT id, name, source, address, phone FROM customers
    WHERE industry='创新型中小企业' AND source LIKE '%经信委%'
    ORDER BY id LIMIT 30""")
print("经信委来源样本:")
for r in c.fetchall():
    print(f"  id={r[0]} name='{r[1][:40]}' source={r[2]} addr={r[3][:30] if r[3] else 'none'} phone={r[4]}")

# 看看有电话的创新型中小企业是哪些
c.execute("""SELECT id, name, source, address FROM customers
    WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''
    ORDER BY id""")
print("\n有电话的创新型中小企业:")
for r in c.fetchall():
    print(f"  id={r[0]} name='{r[1][:40]}' source={r[2]} addr={r[3][:30] if r[3] else 'none'}")

# 看看数据量大但name不是"序号X"的
c.execute("""SELECT COUNT(*) FROM customers
    WHERE industry='创新型中小企业' AND source LIKE '%经信委%'
    AND name NOT LIKE '序号%'
    AND name NOT GLOB '[0-9]*'""")
real_count = c.fetchone()[0]
print(f"\n经信委来源中非序号名称: {real_count}家")

# 看看所有经信委来源
c.execute("""SELECT COUNT(*) FROM customers
    WHERE industry='创新型中小企业' AND source LIKE '%经信委%'""")
total_xinjingwei = c.fetchone()[0]
print(f"经信委来源总计: {total_xinjingwei}家")

# 看看name以中文开头的
c.execute("""SELECT id, name, address FROM customers
    WHERE industry='创新型中小企业' AND source LIKE '%经信委%'
    AND name GLOB '[一-龥]*'
    ORDER BY id LIMIT 10""")
print("\n经信委来源中中文名样本:")
for r in c.fetchall():
    print(f"  id={r[0]} name='{r[1][:40]}' addr={r[2][:30] if r[2] else 'none'}")

conn.close()
