import sqlite3, urllib.parse, urllib.request, json, os

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
LEDGER_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

key = os.environ.get('GD_MAP_KEY', '')
if not key:
    with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    key = data.get('channels', {}).get('高德POI', {}).get('key_source', '').replace('完整32位Key: ', '')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 获取前5个无电话的创新型中小企业
c.execute("""SELECT id, name, address FROM customers
    WHERE industry='创新型中小企业' AND (phone IS NULL OR phone='')
    ORDER BY id LIMIT 5""")
rows = c.fetchall()

for sid, sname, saddr in rows:
    print(f"\n样本: id={sid}, name='{sname[:40]}', addr={saddr[:30] if saddr else 'none'}", flush=True)
    
    kw = urllib.parse.quote(sname + " 重庆")
    url = "https://restapi.amap.com/v3/place/text?key=" + key + "&keywords=" + kw + "&city=500000&offset=1&pageSize=5&output=json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode('utf-8'))
        print(f"  status={data.get('status')}, info={data.get('info')}", flush=True)
        
        for poi in data.get('pois', [])[:3]:
            pn = poi.get('name', '')
            pp = poi.get('tel', '')
            # 检查各种匹配
            m1 = sname[:4] in pn
            m2 = pn[:4] in sname
            m3 = sname[:5] in pn
            m4 = pn[:5] in sname
            print(f"    POI: '{pn[:30]}' | tel={pp} | match4={m1}/{m2} match5={m3}/{m4}", flush=True)
    except Exception as e:
        print(f"  Error: {e}", flush=True)

conn.close()
