"""
为创新型中小企业补抓高德POI电话
策略：使用企业注册名（去掉"创新型中小企业"等后缀），按行业关键词搜索
"""
import sqlite3, json, os, time, random, sys, urllib.parse, re

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
LEDGER_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

DISTRICTS = {
    '渝中区': '500103', '江北区': '500105', '渝北区': '500112',
    '南岸区': '500108', '九龙坡区': '500107', '沙坪坝区': '500106',
    '北碚区': '500109', '大渡口区': '500104', '巴南区': '500113',
    '重庆高新区': '500301',
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

def search_amap(keyword, city='500000', offset=1, page_size=20):
    key = get_amap_key()
    url = f"https://restapi.amap.com/v3/place/text?key={key}&keywords={urllib.parse.quote(keyword)}&city={city}&offset={offset}&pageSize={page_size}&output=json"
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        if data.get('status') == '1':
            return data.get('pois', [])
        else:
            print(f"    API error: {data.get('info')}")
            return []
    except Exception as e:
        print(f"    Request error: {e}")
        return []

def clean_name(name):
    """清理企业名称，去掉序号等噪音"""
    import re
    # 去掉"序号 "前缀
    name = re.sub(r'^序号\s*\d+\s*', '', name)
    # 去掉括号内容（如(2025)）
    name = re.sub(r'\(.*?\)', '', name)
    name = name.strip()
    return name

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取所有创新型中小企业无电话的
    c.execute("""
        SELECT id, name, address, lat, lng
        FROM customers
        WHERE industry = '创新型中小企业'
        AND (phone IS NULL OR phone = '')
    """)
    no_phone = c.fetchall()
    print(f"创新型中小企业无电话: {len(no_phone)}家")
    
    # 行业关键词映射
    industry_keywords = {
        '机械': '机械 重庆', '制造': '制造 重庆', '化工': '化工 重庆',
        '建材': '建材 重庆', '科技': '科技 重庆', '电子': '电子 重庆',
        '能源': '能源 重庆', '环保': '环保 重庆', '材料': '材料 重庆',
        '设备': '设备 重庆', '仪表': '仪表 重庆', '光电': '光电 重庆',
        '仪器': '仪器 重庆', '金属': '金属 重庆', '汽车': '汽车 重庆',
    }
    
    found = 0
    processed = 0
    batch_size = 200
    max_batches = 3  # 先跑3批看效果
    
    for batch_idx in range(max_batches):
        batch = no_phone[batch_idx * batch_size:(batch_idx + 1) * batch_size]
        if not batch:
            break
        
        print(f"\n--- 批次 {batch_idx + 1}/{max_batches} ({len(batch)}家) ---")
        
        for cust_id, raw_name, address, lat, lng in batch:
            name = clean_name(raw_name)
            if not name or len(name) < 3:
                continue
            
            processed += 1
            
            # 根据名称推测行业关键词
            keyword = None
            for kw, search in industry_keywords.items():
                if kw in name:
                    keyword = f"{name} {search}"
                    break
            
            if not keyword:
                keyword = f"{name} 有限公司 重庆"
            
            pois = search_amap(keyword)
            
            if pois:
                for poi in pois:
                    poi_name = poi.get('name', '')
                    poi_phone = poi.get('tel', '')
                    
                    # 模糊匹配：原名或清理后的名字在POI名中
                    if name[:5] in poi_name or poi_name[:5] in name:
                        if poi_phone:
                            c.execute("UPDATE customers SET phone = ? WHERE id = ?", (poi_phone, cust_id))
                            found += 1
                            print(f"  [{processed}] FOUND: {name[:20]}... -> {poi_phone}")
                            time.sleep(0.2)
                            break
            
            if processed % 20 == 0:
                print(f"  Progress: {processed}, found: {found}")
            
            time.sleep(0.15)
        
        time.sleep(random.uniform(3, 5))
    
    conn.commit()
    
    c.execute("""
        SELECT COUNT(*) FROM customers 
        WHERE industry = '创新型中小企业' 
        AND phone IS NOT NULL AND phone != ''
    """)
    new_total = c.fetchone()[0]
    
    print(f"\n{'='*50}")
    print(f"补抓完成!")
    print(f"处理: {processed}家")
    print(f"匹配成功: {found}条")
    print(f"创新型中小企业电话覆盖率: {new_total}/1793 ({new_total/1793*100:.1f}%)")
    print(f"本次新增: {new_total - 12}条")
    
    conn.close()

if __name__ == '__main__':
    main()
