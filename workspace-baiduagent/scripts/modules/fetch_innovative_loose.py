"""创新型中小企业高德POI补电话 - 宽松匹配版"""
import sqlite3, urllib.parse, urllib.request, json, os, time, random, sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
LEDGER_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

AREA_MAP = {'渝中':'500103','江北':'500105','渝北':'500112','南岸':'500108',
            '九龙坡':'500107','沙坪坝':'500106','北碚':'500109','大渡口':'500104',
            '巴南':'500113','高新':'500301','两江':'500105','万州':'500101',
            '涪陵':'500102','永川':'500301','江津':'500116','合川':'500117',
            '长寿':'500112','大足':'500111'}

def get_key():
    key = os.environ.get('GD_MAP_KEY', '')
    if not key:
        try:
            with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            key = data.get('channels', {}).get('高德POI', {}).get('key_source', '').replace('完整32位Key: ', '')
        except: pass
    return key.strip()

def search(kw, city='500000'):
    key = get_key()
    url = "https://restapi.amap.com/v3/place/text?key=" + key + "&keywords=" + urllib.parse.quote(kw) + "&city=" + city + "&offset=1&pageSize=10&output=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode('utf-8'))
        if data.get('status') == '1':
            return data.get('pois', []), data.get('info', '')
        return [], data.get('info', 'ERR')
    except Exception as e:
        return [], str(e)

def has_phone(poi):
    """检查POI是否有有效电话"""
    tel = poi.get('tel', '')
    if not tel:
        return False
    # 过滤无效电话
    import re
    # 去掉括号和空格
    cleaned = re.sub(r'[\s()（）\-]', '', tel)
    # 检查是否包含至少7个数字
    digits = re.findall(r'\d+', cleaned)
    total_digits = sum(len(d) for d in digits)
    return total_digits >= 7

def try_match(name, pois):
    """尝试匹配并返回电话"""
    if not pois:
        return None
    
    # 策略1: 精确匹配（原名包含在POI名中）
    for poi in pois:
        pn = poi.get('name', '')
        pp = poi.get('tel', '')
        if has_phone(poi) and name[:6] in pn:
            return pp
    
    # 策略2: 宽松匹配（去掉"重庆"前缀后匹配）
    name_short = name.replace('重庆', '').replace('市', '')
    for poi in pois:
        pn = poi.get('name', '')
        pp = poi.get('tel', '')
        if has_phone(poi) and (name_short[:5] in pn or pn[:5] in name_short):
            return pp
    
    # 策略3: 最宽松（任意部分匹配）
    for poi in pois:
        pn = poi.get('name', '')
        pp = poi.get('tel', '')
        if has_phone(poi):
            # 检查是否有共同的关键部分（4字以上）
            for i in range(len(name)-3):
                if name[i:i+4] in pn:
                    return pp
    
    return None

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""SELECT id, name, address FROM customers
        WHERE industry='创新型中小企业' AND (phone IS NULL OR phone='')
        ORDER BY id""")
    rows = c.fetchall()
    print(f"剩余无电话创新型中小企业: {len(rows)}家", flush=True)
    
    found = processed = quota_hits = consec_errs = 0
    BATCH_COMMIT = 20
    
    for sid, sname, saddr in rows:
        processed += 1
        city = '500000'
        if saddr:
            for kw, code in AREA_MAP.items():
                if kw in saddr:
                    city = code
                    break
        
        kw_str = sname + " 重庆"
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
                print(f"  连续错误{consec_errs}次(info={info}), 停止", flush=True)
                break
            time.sleep(2)
            continue
        
        consec_errs = 0
        
        phone = try_match(sname, pois)
        if phone:
            c.execute("UPDATE customers SET phone=? WHERE id=?", (phone, sid))
            found += 1
            area_str = ""
            for ak in AREA_MAP:
                if ak in (saddr or ''):
                    area_str = "[" + ak + "]"
                    break
            print(f"  [{processed}] FOUND{area_str}: {sname[:22]}... -> {phone}", flush=True)
            time.sleep(0.3)
        
        if processed % BATCH_COMMIT == 0:
            conn.commit()
            print(f"  [COMMIT] Progress: {processed}, found:{found}", flush=True)
        
        time.sleep(random.uniform(0.4, 0.8))
    
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''")
    total = c.fetchone()[0]
    
    print(f"\n{'='*50}", flush=True)
    print(f"完成! 本次处理:{processed} 新增:{found} 配额超限:{quota_hits}", flush=True)
    print(f"创新型中小企业电话总计: {total}/1793 ({total/1793*100:.1f}%)", flush=True)
    conn.close()

if __name__ == '__main__':
    main()
