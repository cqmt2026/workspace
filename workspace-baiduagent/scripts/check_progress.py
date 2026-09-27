import sqlite3, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM customers WHERE lat IS NOT NULL AND lat != ''")
p = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers")
t = cur.fetchone()[0]
pf = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\coord_progress.json'
prog = 0
if os.path.exists(pf):
    with open(pf, encoding='utf-8') as f:
        prog = json.load(f).get('done', 0)
print(f"已有坐标: {p}/{t} ({p*100//t}%)")
print(f"进度记录: 已处理{prog}条")
conn.close()
