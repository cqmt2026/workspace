"""创新型中小企业高德POI补电话 - 极简测试版，确认API可用后再批量"""
import sqlite3, urllib.parse, urllib.request, json, os, time, re, sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
LEDGER_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

def get_amap_key():
    key = os.environ.get('GD_MAP_KEY', '')
    if not key:
        try:
            with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            key = data.get('channels', {}).get('高德POI', {}).get('key_source', '').replace('完整32位Key: ', '')
        except:
            pass
    return key

def search_amap(keyword, city='500000', page_size=10):
    key = get_amap_key()
    url = f"https://restapi.amap.com/v3/place/text?key={key}&keywords={urllib.parse.quote(keyword)}&city={city}&offset=1&pageSize={page_size}&output=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        if data.get('status') == '1':
            return data.get('pois', []), data.get('info', '')
        else:
            return [], data.get('info', 'UNKNOWN')
    except Exception as e:
        return [], str(e)

def clean_name(name):
    name = re.sub(r'^序号\s*\d+\s*', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\d{4}', '', name)
    return name.strip()

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取样本：经信委来源的无电话客户
    c.execute("""
        SELECT id, name, address FROM customers
        WHERE industry = '创新型中小企业'
        AND (phone IS NULL OR phone = '')
        AND source LIKE '%经信委%'
        ORDER BY id
        LIMIT 30
    """)
    samples = c.fetchall()
    print(f"经信委来源无电话样本: {len(samples)}家")
    
    found = 0
    for sid, sname, saddr in samples:
        name = clean_name(sname)
        if not name or len(name) < 3:
            continue
        
        kw = f"{name} 重庆"
        pois, info = search_amap(kw)
        
        status_icon = "?"
        if info == 'QUOTA_EXCEEDED':
            status_icon = "X"
            print(f"  [!] QUOTA EXCEEDED for: {name[:20]}")
            break
        elif info == 'OK' and pois:
            status_icon = "O"
            # 检查是否有电话
            for poi in pois:
                pn = poi.get('name', '')
                pp = poi.get('tel', '')
                if pp and (name[:4] in pn or pn[:4] in name):
                    c.execute("UPDATE customers SET phone = ? WHERE id = ?", (pp, sid))
                    found += 1
                    print(f"  [{status_icon}] FOUND: {name[:25]}... -> {pp}")
                    break
            else:
                print(f"  [{status_icon}] No match: {name[:25]}... (pois={len(pois)})")
        else:
            print(f"  [ERR] {info}: {name[:20]}")
        
        time.sleep(1.0)
    
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''")
    new_total = c.fetchone()[0]
    
    print(f"\n结果: 找到{found}条, 创新型中小企业总电话: {new_total}/1793")
    conn.close()

if __name__ == '__main__':
    main()
