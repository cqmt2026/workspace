"""
创新型中小企业高德POI补电话 - 全量版
策略：有地址的用地址关键词精搜，无地址的用企业名+行业词广搜
速度优化：每次搜索后随机延迟1-2秒，避开配额限制
"""
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
    name = re.sub(r'\d{4}', '', name)
    return name.strip()

def try_match(name, pois):
    """尝试匹配并返回第一个有效电话"""
    if not pois or len(name) < 3:
        return None
    for poi in pois:
        poi_name = poi.get('name', '')
        poi_phone = poi.get('tel', '')
        if not poi_phone:
            continue
        # 宽松匹配：原名或清理后的名字
        if name[:4] in poi_name or poi_name[:4] in name:
            return poi_phone
        # 更宽松：包含关键部分（5字以上）
        if len(name) >= 5 and (name[:5] in poi_name or poi_name[:5] in name):
            return poi_phone
    return None

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取所有无电话的创新型中小企业
    c.execute("""
        SELECT id, name, address FROM customers
        WHERE industry = '创新型中小企业'
        AND (phone IS NULL OR phone = '')
        ORDER BY id
    """)
    all_customers = c.fetchall()
    print(f"无电话创新型中小企业: {len(all_customers)}家")
    
    # 分离有地址和无地址
    with_addr = [(cid, cname, caddr) for cid, cname, caddr in all_customers if caddr]
    no_addr = [(cid, cname, caddr) for cid, cname, caddr in all_customers if not caddr]
    print(f"  有地址: {len(with_addr)}家")
    print(f"  无地址: {len(no_addr)}家")
    
    found = 0
    processed = 0
    quota_hits = 0
    last_quota_reset = 0
    
    # 处理有地址的（优先）
    print(f"\n--- 批次1: 有地址 {len(with_addr)}家 ---")
    for sid, sname, saddr in with_addr:
        name = clean_name(sname)
        if not name or len(name) < 3:
            continue
        
        processed += 1
        kw = f"{name} 重庆"
        pois, info = search_amap(kw)
        
        if info == 'QUOTA_EXCEEDED':
            quota_hits += 1
            wait = max(30, 60 - (time.time() - last_quota_reset))
            print(f"  [!] 配额超限，等待{wait:.0f}秒...")
            time.sleep(wait)
            last_quota_reset = time.time()
            pois, info = search_amap(kw)
            if info == 'QUOTA_EXCEEDED':
                print(f"  连续超限，停止有地址批次")
                break
        
        phone = try_match(name, pois)
        if phone:
            c.execute("UPDATE customers SET phone = ? WHERE id = ?", (phone, sid))
            found += 1
            print(f"  [{processed}] FOUND: {name[:25]}... -> {phone}")
        
        if processed % 30 == 0:
            print(f"  Progress: {processed}, found: {found}, quota: {quota_hits}")
        
        time.sleep(random.uniform(0.8, 1.5))
    
    conn.commit()
    
    # 处理无地址的（用更通用的搜索）
    print(f"\n--- 批次2: 无地址 {len(no_addr)}家 ---")
    for sid, sname, saddr in no_addr:
        name = clean_name(sname)
        if not name or len(name) < 3:
            continue
        
        processed += 1
        # 无地址时用更通用的搜索
        kw = f"{name} 重庆 有限公司"
        pois, info = search_amap(kw)
        
        if info == 'QUOTA_EXCEEDED':
            quota_hits += 1
            time.sleep(30)
            pois, info = search_amap(kw)
            if info == 'QUOTA_EXCEEDED':
                print(f"  配额持续超限，停止无地址批次")
                break
        
        phone = try_match(name, pois)
        if phone:
            c.execute("UPDATE customers SET phone = ? WHERE id = ?", (phone, sid))
            found += 1
            print(f"  [{processed}] FOUND: {name[:25]}... -> {phone}")
        
        if processed % 30 == 0:
            print(f"  Progress: {processed}, found: {found}, quota: {quota_hits}")
        
        time.sleep(random.uniform(0.8, 1.5))
    
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''")
    new_total = c.fetchone()[0]
    
    print(f"\n{'='*50}")
    print(f"补抓完成!")
    print(f"总处理: {processed}家")
    print(f"匹配成功: {found}条")
    print(f"配额超限: {quota_hits}次")
    print(f"创新型中小企业电话覆盖率: {new_total}/1793 ({new_total/1793*100:.1f}%)")
    print(f"本次新增: {new_total - 12}条")
    
    conn.close()

if __name__ == '__main__':
    main()
