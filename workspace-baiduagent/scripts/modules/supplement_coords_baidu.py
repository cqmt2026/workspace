# -*- coding: utf-8 -*-
"""用百度geocoding补充客户坐标（独立配额，不消耗place）"""
import requests, sys, time, sqlite3, re
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

print("=" * 70)
print("【百度geocoding补充坐标 - 开始执行】")
print("=" * 70)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 查询无坐标的客户
cur.execute("SELECT id, name, address, district FROM customers WHERE lat IS NULL OR lat = '' LIMIT 200")
rows = cur.fetchall()
print(f"待补充坐标: {len(rows)}条")

success = 0
for row in rows:
    cid, name, addr, dist = row
    # 组合地址
    search_addr = f"{name}" if not addr else addr
    if dist:
        search_addr = f"{search_addr} {dist}"
    try:
        r = requests.get('https://api.map.baidu.com/geocoding/v3/',
            params={'ak': AK, 'address': search_addr, 'output': 'json'}, timeout=10)
        d = r.json()
        if d.get('status') == 0 and d.get('result'):
            loc = d['result'].get('location', {})
            lat, lng = loc.get('lat'), loc.get('lng')
            if lat and lng:
                cur.execute("UPDATE customers SET lat=?, lng=? WHERE id=?", (lat, lng, cid))
                success += 1
        time.sleep(0.2)
    except Exception as e:
        pass

conn.commit()

cur.execute("SELECT COUNT(*) FROM customers WHERE lat IS NOT NULL AND lat != ''")
has_coord = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers")
total = cur.fetchone()[0]

print(f"\n✅ 本次补充: {success}条")
print(f"📊 有坐标: {has_coord}/{total} ({has_coord*100//total}%)")
conn.close()
