"""
创新型中小企业高德POI补电话 - 高效版
策略：小批量+慢速+严格匹配，避免触发配额限制
"""
import sqlite3, urllib.parse, urllib.request, json, os, time, re, random
import sqlite3, urllib.parse, urllib.request, json, os, time, re, random, sys

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
        elif data.get('info') == 'CUQPS_HAS_EXCEEDED_THE_LIMIT':
            return [], 'QUOTA_EXCEEDED'
        else:
            return [], data.get('info', 'UNKNOWN')
    except Exception as e:
        return [], str(e)

def clean_name(name):
    name = re.sub(r'^序号\s*\d+\s*', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\d{4}', '', name)  # 去掉年份
    return name.strip()

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取无电话的创新型中小企业（有地址的优先）
    c.execute("""
        SELECT id, name, address FROM customers
        WHERE industry = '创新型中小企业'
        AND (phone IS NULL OR phone = '')
        AND address IS NOT NULL AND address != ''
        ORDER BY id
    """)
    has_addr = c.fetchall()
    
    c.execute("""
        SELECT id, name, address FROM customers
        WHERE industry = '创新型中小企业'
        AND (phone IS NULL OR phone = '')
        AND (address IS NULL OR address = '')
        ORDER BY id
    """)
    no_addr = c.fetchall()
    
    print(f"无电话创新型中小企业: {len(has_addr)}有地址 + {len(no_addr)}无地址 = {len(has_addr)+len(no_addr)}家")
    
    found = 0
    processed = 0
    quota_hit = 0
    
    # 先处理有地址的
    for sid, sname, saddr in has_addr:
        name = clean_name(sname)
        if not name or len(name) < 3:
            continue
        
        processed += 1
        
        # 搜索
        kw = f"{name} 重庆"
        pois, info = search_amap(kw)
        
        if info == 'QUOTA_EXCEEDED':
            quota_hit += 1
            print(f"\n  [!] 配额超限，等待30秒后重试...")
            time.sleep(30)
            # 重试一次
            pois, info = search_amap(kw)
            if info == 'QUOTA_EXCEEDED':
                print(f"  重试仍超限，跳过后续")
                break
        
        if pois:
            for poi in pois:
                poi_name = poi.get('name', '')
                poi_phone = poi.get('tel', '')
                
                # 匹配规则：原名前5位包含在POI名中，或POI名前5位在原名中
                if len(name) >= 5:
                    match = name[:5] in poi_name or poi_name[:5] in name
                else:
                    match = name in poi_name or poi_name in name
                
                if match and poi_phone:
                    c.execute("UPDATE customers SET phone = ? WHERE id = ?", (poi_phone, sid))
                    found += 1
                    print(f"  [{processed}] FOUND: {name[:25]}... -> {poi_phone}")
                    time.sleep(0.5)
                    break
        
        # 每50条暂停一下
        if processed % 50 == 0:
            print(f"  Progress: {processed}, found: {found}, quota_hits: {quota_hit}")
            time.sleep(random.uniform(2, 4))
        
        # 每条之间小延迟
        time.sleep(0.3)
    
    conn.commit()
    
    # 统计
    c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''")
    new_total = c.fetchone()[0]
    
    print(f"\n{'='*50}")
    print(f"补抓完成!")
    print(f"处理: {processed}家")
    print(f"匹配成功: {found}条")
    print(f"配额超限次数: {quota_hit}")
    print(f"创新型中小企业电话: {new_total}/1793 ({new_total/1793*100:.1f}%)")
    
    conn.close()

if __name__ == '__main__':
    main()
