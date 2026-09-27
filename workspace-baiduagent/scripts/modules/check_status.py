import sqlite3, os
db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
master = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM customers")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
has_phone = c.fetchone()[0]
print(f"CRM总数: {total}")
print(f"有电话: {has_phone} ({has_phone*100//total}%)")
print(f"\n机械行业: 总数893, 有电话241")
# 检查master目录中的机械相关csv
files = [f for f in os.listdir(master) if '机械' in f or 'mechanics' in f.lower()]
print(f"\nmaster目录中机械相关文件: {files}")
# 检查ledger
ledger_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'
if os.path.exists(ledger_path):
    import json
    with open(ledger_path, 'r', encoding='utf-8') as f:
        ledger = json.load(f)
    if '机械装备汽配' in ledger.get('industries', {}):
        print(f"\n台账记录: {ledger['industries']['机械装备汽配']}")
    else:
        print("\n台账中暂无机械装备汽配记录")
conn.close()