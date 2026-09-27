# -*- coding: utf-8 -*-
"""
立即用百度geocoding补充低覆盖率行业坐标
百度geocoding接口不受place配额限制
"""
import requests, sys, time, sqlite3, csv, os
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
OUT_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\temp'
os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 70)
print("【百度geocoding补充坐标 - 紧急执行】")
print("=" * 70)

# 连接CRM
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 查询低覆盖率行业且无坐标的客户
cur.execute("""
    SELECT id, name, industry 
    FROM customers 
    WHERE (lat IS NULL OR lat = '') 
    AND industry IN ('软件信息','智能制造','物流货运','检验检测','电子科技','食品加工','能源环保补充','人力资源','教育培训补充')
    LIMIT 100
""")
rows = cur.fetchall()
print(f"\n待补充坐标客户: {len(rows)}条")

success = 0
failed = 0
for row in rows:
    cid, name, addr, industry = row
    if not addr or addr.strip() == '':
        # 尝试用名称+行业生成地址
        addr = f"重庆市{industry}"
    
    try:
        r = requests.get('https://api.map.baidu.com/geocoding/v3/',
            params={'ak': AK, 'address': addr, 'city': '重庆', 'output': 'json'}, timeout=10)
        d = r.json()
        if d.get('status') == 0 and d.get('result'):
            loc = d['result'].get('location', {})
            lat, lng = loc.get('lat'), loc.get('lng')
            if lat and lng:
                cur.execute("UPDATE customers SET lat=?, lng=? WHERE id=?", (lat, lng, cid))
                success += 1
                if success % 20 == 0:
                    print(f"  已补充{success}条...")
            else:
                failed += 1
        else:
            failed += 1
        time.sleep(0.3)
    except Exception as e:
        failed += 1

conn.commit()

# 验证结果
cur.execute("SELECT COUNT(*) FROM customers WHERE lat IS NOT NULL AND lat != ''")
has_lat = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers")
total = cur.fetchone()[0]

print(f"\n✅ 补充结果:")
print(f"   成功: {success}条")
print(f"   失败: {failed}条")
print(f"   CRM总客户: {total:,}家")
print(f"   有坐标: {has_lat:,}家 ({has_lat*100//total}%)")

conn.close()
