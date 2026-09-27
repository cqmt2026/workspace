import sqlite3
conn=sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c=conn.cursor()
c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''")
print('创新型中小企业有电话:', c.fetchone()[0])
conn.close()
