# -*- coding: utf-8 -*-
"""百度geocoding补充坐标 - 使用正确字段名"""
import requests, sys, time, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

print("=" * 70)
print("【百度geocoding补充坐标】")
print("=" * 70)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 检查实际字段
cur.execute("PRAGMA table_info(customers)")
cols = [r[1] for r in cur.fetchall()]
print(f"CRM字段: {cols}")

# 低覆盖率行业
industries = ['软件信息','智能制造','物流货运','检验检测','电子科技',
              '食品加工','能源环保补充','人力资源','教育培训补充','创新型中小企业']

# 查询无坐标的客户（假设坐标字段是lng/lat）
cur.execute(f"""
    SELECT id, name, industry 
    FROM customers 
    WHERE lng IS NULL OR lng = ''
    AND industry IN ({','.join(['?']*len(industries))})
    LIMIT 50
""", industries)
rows = cur.fetchall()
print(f"\n待补充客户: {len(rows)}条")

success = 0
for row in rows:
    cid, name, industry = row
    addr = f"重庆市{industry}"
    try:
        r = requests.get('https://api.map.baidu.com/geocoding/v3/',
            params={'ak': AK, 'address': addr, 'city': '重庆', 'output': 'json'}, timeout=10)
        d = r.json()
        if d.get('status') == 0 and d.get('result'):
            loc = d['result'].get('location', {})
            lat, lng = loc.get('lat'), loc.get('lng')
            if lat and lng:
                cur.execute("UPDATE customers SET lng=?, lat=? WHERE id=?", (lng, lat, cid))
                success += 1
        time.sleep(0.3)
    except:
        pass

conn.commit()
cur.execute("SELECT COUNT(*) FROM customers WHERE lng IS NOT NULL AND lng != ''")
has_coord = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers")
total = cur.fetchone()[0]

print(f"\n✅ 补充成功: {success}条")
print(f"📊 有坐标: {has_coord}/{total} ({has_coord*100//total}%)")
conn.close()
