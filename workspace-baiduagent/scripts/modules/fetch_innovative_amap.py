# -*- coding: utf-8 -*-
"""
高德POI批量补抓 - 创新型中小企业
"""
import sys, os, time, sqlite3, requests, json
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

# 高德API Key (从MEMORY读取)
GAODE_KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
GAODE_BASE = 'https://restapi.amap.com/v3/place/text'

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# 重庆主城9区 + 万州/涪陵
DISTRICTS = [
    ('渝中区', 29.556, 106.577),
    ('江北区', 29.578, 106.530),
    ('南岸区', 29.536, 106.573),
    ('九龙坡区', 29.508, 106.486),
    ('沙坪坝区', 29.559, 106.389),
    ('渝北区', 29.713, 106.625),
    ('巴南区', 29.398, 106.551),
    ('北碚区', 29.847, 106.411),
    ('大渡口区', 29.457, 106.485),
    ('高新区', 29.569, 106.453),
    ('万州区', 30.818, 108.398),
    ('涪陵区', 29.698, 107.396),
]

KEYWORDS = [
    '科技有限公司',
    '机械有限公司', 
    '工贸有限公司',
    '实业有限公司',
    '建材有限公司',
    '新能源科技',
    '生物科技',
    '电子科技',
    '自动化设备',
    '医疗器械',
]

def fetch_amap(keyword, district, lat, lng, page=1):
    """高德POI搜索"""
    params = {
        'keywords': keyword,
        'city': '重庆',
        'citylimit': 'true',
        'offset': 20,
        'page': page,
        'key': GAODE_KEY,
        'location': f'{lng},{lat}',
        'radius': 5000,  # 5公里范围
        'extensions': 'all',
    }
    
    try:
        r = requests.get(GAODE_BASE, params=params, timeout=15, headers=HEADERS)
        d = r.json()
        
        if d.get('status') != '1':
            return [], d.get('info', 'error')
        
        pois = d.get('pois', [])
        return pois, 'ok'
        
    except Exception as e:
        return [], str(e)

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("=" * 70)
    print("【创新型中小企业 - 高德POI批量补抓】")
    print("=" * 70)
    
    # 统计当前状态
    c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%'")
    total_before = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%' AND phone IS NOT NULL AND phone != ''")
    phone_before = c.fetchone()[0]
    
    print(f"\n补抓前:")
    print(f"  总数: {total_before}家")
    print(f"  有电话: {phone_before}家 ({phone_before*100//total_before if total_before>0 else 0}%)")
    
    updated = 0
    searched = 0
    quota_hit = False
    
    for district_name, lat, lng in DISTRICTS:
        if quota_hit:
            break
            
        print(f"\n【{district_name}】")
        
        for kw in KEYWORDS:
            if quota_hit:
                break
            
            for page in range(5):  # 每个关键词最多5页
                if quota_hit:
                    break
                
                pois, info = fetch_amap(kw, district_name, lat, lng, page+1)
                
                if info != 'ok':
                    if 'INVALID_USER_KEY' in info.upper():
                        print(f"  Key错误: {info}")
                        break
                    elif 'QUOTA' in info.upper() or 'LIMIT' in info.upper():
                        quota_hit = True
                        print(f"  配额耗尽")
                    break
                
                if not pois:
                    break
                
                searched += len(pois)
                
                for poi in pois:
                    name = poi.get('name', '').strip()
                    tel = poi.get('tel', '')
                    addr = poi.get('address', '')
                    
                    # 只更新创新型中小企业
                    c.execute("""
                        SELECT id FROM customers 
                        WHERE name = ? 
                        AND industry LIKE '%创新型%'
                        AND (phone IS NULL OR phone = '' OR phone = '无')
                    """, (name,))
                    
                    row = c.fetchone()
                    if row and tel:
                        # 取第一个电话
                        phone = tel.split(',')[0].strip()
                        
                        c.execute("""
                            UPDATE customers 
                            SET phone = ?, address = COALESCE(address, ?),
                                source = source || '+高德POI补抓',
                                updated_at = ?
                            WHERE id = ?
                        """, (phone, addr, datetime.now().strftime('%Y-%m-%d %H:%M'), row[0]))
                        
                        if c.rowcount > 0:
                            updated += 1
                
                time.sleep(0.2)
        
        print(f"  → 已更新{updated}条")
    
    conn.commit()
    conn.close()
    
    # 最终统计
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%'")
    total_after = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%' AND phone IS NOT NULL AND phone != ''")
    phone_after = c.fetchone()[0]
    conn.close()
    
    print(f"\n{'='*70}")
    print(f"补抓完成!")
    print(f"  搜索: {searched}条")
    print(f"  更新电话: {updated}条")
    print(f"  总数: {total_before} → {total_after}家")
    print(f"  有电话: {phone_before} → {phone_after}家 ({phone_after*100//total_after if total_after>0 else 0}%)")

if __name__ == '__main__':
    main()