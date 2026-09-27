# -*- coding: utf-8 -*-
"""腾讯geocoder地址解析 - 补充现有客户坐标数据"""
import requests, sys, time, sqlite3, csv, os
sys.stdout.reconfigure(encoding='utf-8')

TX_KEY = 'JGGBZ-D5I6Q-66H5K-22SMU-I5VXO-NDFLJ'
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

print("=== 腾讯geocoder地址解析补充 ===")
print("可用接口: geocoder (地址→坐标)")
print("目标: 补充现有CRM客户缺失的经纬度")
print()

# 连接数据库
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 查询缺少坐标的客户
cur.execute("""
    SELECT id, name, address 
    FROM customers 
    WHERE (lat IS NULL OR lat = '') AND address IS NOT NULL AND address != ''
    LIMIT 50
""")
no_lat = cur.fetchall()
print(f"缺少坐标的客户: {len(no_lat)}条（本次处理前50条）")

success = 0
for row in no_lat:
    cid, name, addr = row
    try:
        r = requests.get('https://apis.map.qq.com/ws/geocoder/v1',
            params={'key': TX_KEY, 'address': addr, 'region': '重庆'}, timeout=10)
        d = r.json()
        if d.get('status') == 0:
            loc = d.get('result', {}).get('location', {})
            lat, lng = loc.get('lat', 0), loc.get('lng', 0)
            if lat and lng:
                cur.execute("UPDATE customers SET lat=?, lng=? WHERE id=?", (lat, lng, cid))
                success += 1
                if success % 10 == 0:
                    print(f"  已补充{success}条...")
        time.sleep(0.5)
    except Exception as e:
        print(f"  ❌ {name}: {e}")

conn.commit()
print(f"\n✅ 本次补充坐标: {success}条")
conn.close()
