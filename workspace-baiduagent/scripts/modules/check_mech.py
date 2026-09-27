import sqlite3
conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%机械%'")
print(f'机械行业总数: {c.fetchone()[0]}')
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%机械%' AND phone IS NOT NULL AND phone != ''")
print(f'有电话: {c.fetchone()[0]}')
conn.close()