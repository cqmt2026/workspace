"""
为创新型中小企业补抓高德POI电话
目标：通过高德地图搜索"创新型中小企业"名称，获取含电话的数据
策略：按区域分批次搜索，每批最多100条
"""
import sqlite3, json, os, time, random, sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
LEDGER_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

# 重庆主城区9区adcode
DISTRICTS = {
    '渝中区': '500103',
    '江北区': '500105',
    '渝北区': '500112',
    '南岸区': '500108',
    '九龙坡区': '500107',
    '沙坪坝区': '500106',
    '北碚区': '500109',
    '大渡口区': '500104',
    '巴南区': '500113',
    '重庆高新区': '500301',  # 高新区用永川adcode近似
}

def get_amap_key():
    key = os.environ.get('GD_MAP_KEY', '')
    if not key:
        # 尝试从ledger读取
        try:
            with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            key = data.get('channels', {}).get('高德POI', {}).get('key_source', '').replace('完整32位Key: ', '')
        except:
            pass
    return key

def search_amap(keyword, adcode, offset=1, page_size=50):
    """高德POI搜索"""
    import urllib.request
    
    key = get_amap_key()
    if not key or len(key) < 20:
        print(f"  ERROR: Invalid API key (len={len(key)})")
        return []
    
    url = f"https://restapi.amap.com/v3/place/text?key={key}&keywords={keyword}&city={adcode}&offset={offset}&pageSize={page_size}&output=json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        if data.get('status') == '1':
            return data.get('pois', [])
        else:
            print(f"  API error: status={data.get('status')}, info={data.get('info')}")
            return []
    except Exception as e:
        print(f"  Request error: {e}")
        return []

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取所有创新型中小企业（无电话的）
    c.execute("""
        SELECT id, name, address, lat, lng
        FROM customers
        WHERE industry = '创新型中小企业'
        AND (phone IS NULL OR phone = '')
    """)
    no_phone_customers = c.fetchall()
    print(f"创新型中小企业无电话总数: {len(no_phone_customers)}")
    
    # 按区域分组
    by_district = {}
    for cust in no_phone_customers:
        addr = cust[2] or ''
        district = None
        for dist_name, adcode in DISTRICTS.items():
            if dist_name in addr:
                district = dist_name
                break
        if district is None and cust[3] and cust[4]:
            # 有坐标但无区域，尝试根据地址关键词推断
            district = '重庆高新区'  # 默认
        by_district.setdefault(district, []).append(cust)
    
    print(f"\n按区域分布:")
    for d, items in sorted(by_district.items(), key=lambda x: -len(x[1])):
        print(f"  {d or '(未知)'}: {len(items)}家")
    
    # 开始补抓
    found_updates = 0
    total_queries = 0
    success_queries = 0
    no_result_queries = 0
    
    # 使用关键词：企业名称前缀 + 行业词
    keywords = ['有限责任公司', '有限公司', '工贸', '科技', '制造', '机械', '化工', '建材']
    
    for cust_id, name, address, lat, lng in no_phone_customers[:500]:  # 先处理前500家
        # 尝试用企业名搜索
        query_name = name.replace('重庆', '').replace('市', '').strip()
        
        # 优先用地址对应的adcode
        district = None
        for dist_name, adcode in DISTRICTS.items():
            if dist_name in (address or ''):
                district = dist_name
                break
        
        adcode = DISTRICTS.get(district, '500000')  # 重庆全市
        
        # 搜索：企业名 + 行业关键词
        keyword = f"{query_name} 重庆"
        pois = search_amap(keyword, adcode)
        total_queries += 1
        
        if not pois:
            no_result_queries += 1
            continue
        
        # 尝试匹配
        for poi in pois:
            poi_name = poi.get('name', '')
            poi_phone = poi.get('tel', '')
            
            # 简单模糊匹配：包含关键名称部分
            if query_name[:4] in poi_name or poi_name[:4] in query_name:
                if poi_phone:
                    # 更新数据库
                    c.execute("UPDATE customers SET phone = ? WHERE id = ?", (poi_phone, cust_id))
                    found_updates += 1
                    success_queries += 1
                    print(f"  FOUND: {name} -> {poi_phone}")
                    time.sleep(0.3)
                    break
        
        # 随机延迟，避免被限流
        if total_queries % 50 == 0:
            print(f"\n  Progress: {total_queries} queries, {found_updates} matched, {success_queries} success")
            time.sleep(random.uniform(2, 5))
    
    conn.commit()
    
    # 统计结果
    c.execute("""
        SELECT COUNT(*) FROM customers 
        WHERE industry = '创新型中小企业' 
        AND phone IS NOT NULL AND phone != ''
    """)
    new_total = c.fetchone()[0]
    
    print(f"\n{'='*50}")
    print(f"补抓完成!")
    print(f"查询总数: {total_queries}")
    print(f"成功匹配: {success_queries}")
    print(f"无结果: {no_result_queries}")
    print(f"创新型中小企业电话覆盖率: {new_total}/1793 ({new_total/1793*100:.1f}%)")
    print(f"本次新增: {new_total - 12}条")
    
    conn.close()

if __name__ == '__main__':
    main()
