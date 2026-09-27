"""
创新型中小企业高德POI补电话 - 批量版
策略：先获取高德配额测试，确认正常后批量处理
配额保护：连续失败3次暂停，超限暂停60秒
"""
import sqlite3, urllib.parse, urllib.request, json, os, time, re, random, sys

sys.stdout.reconfigure(encoding='utf-8')

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

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取所有无电话的创新型中小企业
    c.execute("""SELECT id, name, address FROM customers
        WHERE industry='创新型中小企业' AND (phone IS NULL OR phone='')
        ORDER BY id""")
    rows = c.fetchall()
    print(f"无电话创新型中小企业: {len(rows)}家")
    
    found = processed = quota_hits = consecutive_errs = 0
    LAST_QUOTA = 0
    
    for sid, sname, saddr in rows:
        name = clean(sname)
        if not name or len(name) < 3:
            continue
        
        processed += 1
        
        # 确定城市code
        city = '500000'
        for kw, code in AREA_MAP.items():
            if kw in (saddr or ''):
                city = code
                break
        
        # 搜索
        kw_str = f"{name} 重庆"
        pois, info = search(kw_str, city)
        
        if info == 'QUOTA_EXCEEDED':
            quota_hits += 1
            wait = max(30, 60 - (time.time() - LAST_QUOTA))
            if processed % 10 == 1:
                print(f"  [!] 配额超限, 等待{wait:.0f}s...")
            time.sleep(wait)
            LAST_QUOTA = time.time()
            pois, info = search(kw_str, city)
            if info == 'QUOTA_EXCEEDED':
                print(f"  持续超限, 停止")
                break
        
        if info != 'OK':
            consecutive_errs += 1
            if consecutive_errs > 5:
                print(f"  连续错误{consecutive_errs}次, 可能配额耗尽, 停止")
                break
            time.sleep(2)
            continue
        
        consecutive_errs = 0
        
        # 匹配
        if pois:
            for poi in pois:
                pn = poi.get('name', '')
                pp = poi.get('tel', '')
                if pp and (name[:4] in pn or pn[:4] in name):
                    c.execute("UPDATE customers SET phone=? WHERE id=?", (pp, sid))
                    found += 1
                    area_str = f"[{kw}]" if any(kw in (saddr or '') for kw in AREA_MAP) else ""
                    print(f"  [{processed}] FOUND{area_str}: {name[:22]}... -> {pp}")
                    time.sleep(0.3)
                    break
        
        # 进度日志
        if processed % 10 == 0:
            print(f"  Progress: {processed}, found:{found}, quota:{quota_hits}")
        
        time.sleep(random.uniform(0.5, 1.2))
    
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''")
    total = c.fetchone()[0]
    
    print(f"\n{'='*50}")
    print(f"完成! 处理:{processed} 新增:{found} 配额超限:{quota_hits}")
    print(f"创新型中小企业电话: {total}/1793 ({total/1793*100:.1f}%)")
    conn.close()

if __name__ == '__main__':
    main()
