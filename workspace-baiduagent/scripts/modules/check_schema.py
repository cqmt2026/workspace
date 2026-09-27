import sqlite3
db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
c = conn.cursor()
# 查看表结构
c.execute("PRAGMA table_info(customers)")
cols = c.fetchall()
print("=== customers表字段 ===")
for col in cols:
    print(col)
conn.close()