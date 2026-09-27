"""创新型中小企业高德POI补电话 - 无缓冲版"""
import sqlite3, urllib.parse, urllib.request, json, os, time, re, random, sys

# 无缓冲输出
sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1, encoding='utf-8')
sys.stderr = open(sys.stderr.fileno(), mode='w', buffering=1, encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
LEDGER_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

AREA_MAP = {'渝中':'500103','江北':'500105','渝北':'500112','南岸':'500108',
            '九龙坡':'500107','沙坪坝':'500106','北碚':'500109','大渡口':'500104',
            '巴南':'500113','高新':'500301','两江':'500105'}

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

print(f"开始补抓创新型中小企业...", flush=True)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""SELECT id, name, address FROM customers
    WHERE industry='创新型中小企业' AND (phone IS NULL OR phone='')
    ORDER BY id""")
rows = c.fetchall()
print(f"无电话创新型中小企业: {len(rows)}家", flush=True)

found = processed = quota_hits = consec_errs = 0

for sid, sname, saddr in rows:
    name = clean(sname)
    if not name or len(name) < 3:
        continue
    
    processed += 1
    city = '500000'
    for kw, code in AREA_MAP.items():
        if kw in (saddr or ''):
            city = code
            break
    
    kw_str = f"{name} 重庆"
    pois, info = search(kw_str, city)
    
    if info == 'QUOTA_EXCEEDED':
        quota_hits += 1
        print(f"  [!] 配额超限({quota_hits}), 等待30秒...", flush=True)
        time.sleep(30)
        pois, info = search(kw_str, city)
        if info == 'QUOTA_EXCEEDED':
            print(f"  持续超限, 停止", flush=True)
            break
        continue
    
    if info != 'OK':
        consec_errs += 1
        if consec_errs > 5:
            print(f"  连续错误{consec_errs}次, 停止", flush=True)
            break
        time.sleep(2)
        continue
    
    consec_errs = 0
    
    if pois:
        for poi in pois:
            pn = poi.get('name', '')
            pp = poi.get('tel', '')
            if pp and (name[:4] in pn or pn[:4] in name):
                c.execute("UPDATE customers SET phone=? WHERE id=?", (pp, sid))
                found += 1
                area_str = ""
                for ak in AREA_MAP:
                    if ak in (saddr or ''):
                        area_str = f"[{ak}]"
                        break
                print(f"  [{processed}] FOUND{area_str}: {name[:22]}... -> {pp}", flush=True)
                time.sleep(0.3)
                break
    
    if processed % 10 == 0:
        print(f"  Progress: {processed}, found:{found}, quota:{quota_hits}", flush=True)
    
    time.sleep(random.uniform(0.5, 1.0))

conn.commit()

c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''")
total = c.fetchone()[0]

print(f"\n{'='*50}", flush=True)
print(f"完成! 处理:{processed} 新增:{found} 配额超限:{quota_hits}", flush=True)
print(f"创新型中小企业电话: {total}/1793 ({total/1793*100:.1f}%)", flush=True)
conn.close()
print("Done!", flush=True)
