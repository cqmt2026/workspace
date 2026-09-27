# -*- coding: utf-8 -*-
"""
创新型中小企业电话补抓 - 简化版
直接按区县+企业类型批量搜索百度POI
"""
import sys, time, sqlite3, requests, json
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

BAIDU_AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BAIDU_BASE = 'https://api.map.baidu.com/place/v2/search'
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

DISTRICTS = ['万州区', '涪陵区', '渝中区', '大渡口区', '江北区', '沙坪坝区', 
             '九龙坡区', '南岸区', '北碚区', '渝北区', '巴南区', '高新区', '两江新区']

KEYWORDS = ['科技有限公司', '机械有限公司', '建材有限公司', '食品有限公司', 
            '实业有限公司', '贸易有限公司', '新能源科技', '生物科技']

def fetch_poi(keyword, district, page=0):
    params = {
        'query': keyword,
        'output': 'json',
        'ak': BAIDU_AK,
        'page_size': 20,
        'page_num': page,
        'scope': 2,
        'region': district if district else '重庆',
    }
    try:
        r = requests.get(BAIDU_BASE, params=params, timeout=10, headers=HEADERS)
        d = r.json()
        if d.get('status') == 0:
            return d.get('results', []), 'ok'
        return [], d.get('info', 'error')
    except:
        return [], 'exception'

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("=" * 60)
    print("【创新型中小企业电话补抓】")
    print("=" * 60)
    
    # 先看看无电话的有多少
    c.execute("""
        SELECT COUNT(*) FROM customers 
        WHERE industry LIKE '%创新型%' 
        AND (phone IS NULL OR phone = '' OR phone = '无')
    """)
    no_phone_count = c.fetchone()[0]
    print(f"无电话客户: {no_phone_count}家\n")
    
    # 按区县逐个搜索
    updated = 0
    quota_hit = False
    
    for district in DISTRICTS:
        if quota_hit:
            break
            
        print(f"【{district}】")
        
        for kw in KEYWORDS:
            if quota_hit:
                break
                
            for page in range(5):  # 每关键词最多5页
                if quota_hit:
                    break
                    
                results, info = fetch_poi(kw, district, page)
                
                if info != 'ok':
                    if 'LIMIT' in info.upper() or 'QUOTA' in info.upper():
                        quota_hit = True
                        print(f"  ⚠️ 配额耗尽")
                    break
                
                if not results:
                    break
                
                for item in results:
                    name = item.get('name', '').strip()
                    tel = item.get('tel', '') or item.get('telephone', '') or ''
                    addr = item.get('address', '')
                    area = item.get('area', '')
                    
                    # 检查是否创新型中小企业且无电话
                    c.execute("""
                        SELECT id FROM customers 
                        WHERE name = ? AND industry LIKE '%创新型%'
                        AND (phone IS NULL OR phone = '' OR phone = '无')
                    """, (name,))
                    
                    row = c.fetchone()
                    if row and tel:
                        c.execute("""
                            UPDATE customers 
                            SET phone = ?, address = COALESCE(address, ?),
                                source = source || '+百度POI补抓',
                                updated_at = ?
                            WHERE id = ?
                        """, (tel, addr, datetime.now().strftime('%Y-%m-%d %H:%M'), row[0]))
                        
                        if c.rowcount > 0:
                            updated += 1
                            if updated % 10 == 0:
                                print(f"  ✓ 已更新{updated}条")
                
                time.sleep(0.3)
        
        # 每区县保存进度
        progress = {
            'district': district,
            'updated': updated,
            'timestamp': datetime.now().isoformat()
        }
        print(f"  → 本轮更新{updated}条")
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"补抓完成: 更新{updated}条电话")

if __name__ == '__main__':
    main()