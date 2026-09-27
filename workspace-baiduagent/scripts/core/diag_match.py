"""诊断：为什么匹配率为0？"""
import sqlite3, urllib.parse, urllib.request, json, os, time, re, sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
LEDGER_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

def get_key():
    key = os.environ.get('GD_MAP_KEY', '')
    if not key:
        try:
            with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            key = data.get('channels', {}).get('高德POI', {}).get('key_source', '').replace('完整32位Key: ', '')
        except: pass
    return key

def search(kw, city='500000'):
    key = get_key()
    url = f"https://restapi.amap.com/v3/place/text?key={key}&keywords={urllib.parse.quote(kw)}&city={city}&offset=1&pageSize=10&output=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode('utf-8'))
        if data.get('status') == '1':
            return data.get('pois', []), data.get('info', '')
        return [], data.get('info', 'ERR')
    except Exception as e:
        return [], str(e)

def clean(n):
    n = re.sub(r'^序号\s*\d+\s*', '', n)
    n = re.sub(r'\(.*?\)', '', n)
    n = re.sub(r'\d{4}', '', n)
    return n.strip()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 获取前20个经信委来源的样本
c.execute("""SELECT id, name, address FROM customers
    WHERE industry='创新型中小企业' AND (phone IS NULL OR phone='')
    AND source LIKE '%经信委%'
    ORDER BY id LIMIT 20""")
rows = c.fetchall()
print(f"经信委样本: {len(rows)}家\n", flush=True)

for sid, sname, saddr in rows:
    name = clean(sname)
    if not name or len(name) < 3:
        print(f"  SKIP: '{sname[:30]}' (too short after clean)", flush=True)
        continue
    
    kw_str = f"{name} 重庆"
    pois, info = search(kw_str)
    
    print(f"\n搜索: '{name}' (id={sid})", flush=True)
    print(f"  info={info}, pois={len(pois)}", flush=True)
    
    if pois:
        print("  POI结果:", flush=True)
        for poi in pois[:5]:
            pn = poi.get('name', '')
            pp = poi.get('tel', '')
            # 检查各种匹配
            m1 = name[:4] in pn
            m2 = pn[:4] in name
            m3 = name[:5] in pn
            m4 = pn[:5] in name
            print(f"    '{pn[:30]}' | tel={pp} | match4={m1}/{m2} match5={m3}/{m4}", flush=True)
    
    time.sleep(1.0)

conn.close()
print("\n诊断完成", flush=True)
