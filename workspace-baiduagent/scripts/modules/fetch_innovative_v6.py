"""创新型中小企业高德POI补电话 - 快速版：用地址字段匹配区域关键词，提升搜索精度"""
import sqlite3, urllib.parse, urllib.request, json, os, time, re, random, sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
LEDGER_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

# 区域关键词 -> adcode 映射
AREA_KEYWORDS = {
    '渝中': '500103', '江北': '500105', '渝北': '500112', '南岸': '500108',
    '九龙坡': '500107', '沙坪坝': '500106', '北碚': '500109', '大渡口': '500104',
    '巴南': '500113', '高新': '500301', '两江': '500105',
}

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
        elif data.get('info') == 'CUQPS_HAS_EXCEEDED_THE_LIMIT':
            return [], 'QUOTA_EXCEEDED'
        else:
            return [], data.get('info', 'UNKNOWN')
    except Exception as e:
        return [], str(e)

def clean_name(name):
    name = re.sub(r'^序号\s*\d+\s*', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\d{4}', '', name)
    return name.strip()

def get_district(address):
    if not address:
        return None, '500000'
    for kw, code in AREA_KEYWORDS.items():
        if kw in address:
            return kw, code
    return None, '500000'

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
        SELECT id, name, address FROM customers
        WHERE industry = '创新型中小企业'
        AND (phone IS NULL OR phone = '')
        ORDER BY id
    """)
    all_customers = c.fetchall()
    print(f"无电话创新型中小企业: {len(all_customers)}家")
    
    # 预处理：给每个客户加上区域adcode
    customers_with_area = []
    for sid, sname, saddr in all_customers:
        name = clean_name(sname)
        area_kw, adcode = get_district(saddr)
        customers_with_area.append((sid, name, saddr, area_kw, adcode))
    
    found = 0
    processed = 0
    quota_hits = 0
    last_quota_reset = 0
    
    for sid, name, saddr, area_kw, adcode in customers_with_area:
        if not name or len(name) < 3:
            continue
        
        processed += 1
        
        # 用区域adcode搜索，提高精准度
        kw = f"{name} 重庆"
        pois, info = search_amap(kw, city=adcode)
        
        if info == 'QUOTA_EXCEEDED':
            quota_hits += 1
            wait = max(30, 60 - (time.time() - last_quota_reset))
            if processed % 20 == 1:
                print(f"  [!] 配额超限，等待{wait:.0f}秒...")
            time.sleep(wait)
            last_quota_reset = time.time()
            pois, info = search_amap(kw, city=adcode)
            if info == 'QUOTA_EXCEEDED':
                print(f"  持续超限，跳过剩余")
                break
        
        if pois:
            for poi in pois:
                poi_name = poi.get('name', '')
                poi_phone = poi.get('tel', '')
                if not poi_phone:
                    continue
                if name[:4] in poi_name or poi_name[:4] in name:
                    c.execute("UPDATE customers SET phone = ? WHERE id = ?", (poi_phone, sid))
                    found += 1
                    area_str = f" [{area_kw}]" if area_kw else ""
                    print(f"  [{processed}] FOUND{area_str}: {name[:25]}... -> {poi_phone}")
                    time.sleep(0.5)
                    break
        
        if processed % 20 == 0:
            print(f"  Progress: {processed}, found: {found}, quota: {quota_hits}")
        
        time.sleep(random.uniform(0.5, 1.0))
    
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''")
    new_total = c.fetchone()[0]
    
    print(f"\n{'='*50}")
    print(f"处理: {processed}家, 匹配: {found}条, 配额超限: {quota_hits}次")
    print(f"创新型中小企业电话覆盖率: {new_total}/1793 ({new_total/1793*100:.1f}%)")
    print(f"本次新增: {new_total - 12}条")
    
    conn.close()

if __name__ == '__main__':
    main()
