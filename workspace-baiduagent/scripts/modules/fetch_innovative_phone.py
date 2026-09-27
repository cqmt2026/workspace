# -*- coding: utf-8 -*-
"""
创新型中小企业电话补抓脚本
使用高德/百度POI API获取电话
"""
import sys, os, time, sqlite3, requests, json
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

# ========== 配置 ==========
BAIDU_AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
BAIDU_BASE = 'https://api.map.baidu.com/place/v2/search'

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
OUT_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# 区县坐标(用于分区域搜索)
DISTRICTS = {
    '万州区': {'lat': 30.818, 'lng': 108.398},
    '涪陵区': {'lat': 29.698, 'lng': 107.396},
    '渝中区': {'lat': 29.556, 'lng': 106.577},
    '大渡口区': {'lat': 29.457, 'lng': 106.485},
    '江北区': {'lat': 29.578, 'lng': 106.530},
    '沙坪坝区': {'lat': 29.559, 'lng': 106.389},
    '九龙坡区': {'lat': 29.508, 'lng': 106.486},
    '南岸区': {'lat': 29.536, 'lng': 106.573},
    '北碚区': {'lat': 29.847, 'lng': 106.411},
    '渝北区': {'lat': 29.713, 'lng': 106.625},
    '巴南区': {'lat': 29.398, 'lng': 106.551},
    '高新区': {'lat': 29.569, 'lng': 106.453},
    '两江新区': {'lat': 29.605, 'lng': 106.590},
}

def fetch_baidu_poi(keyword, district=None, center=None, page=0):
    """百度POI搜索"""
    params = {
        'query': keyword,
        'output': 'json',
        'ak': BAIDU_AK,
        'page_size': 20,
        'page_num': page,
        'scope': 2,
    }
    
    if district and center:
        params['region'] = district
        params['location'] = f"{center['lng']},{center['lat']}"
    else:
        params['region'] = '重庆'
    
    try:
        r = requests.get(BAIDU_BASE, params=params, timeout=10, headers=HEADERS)
        d = r.json()
        
        if d.get('status') != 0:
            return [], d.get('info', 'unknown')
        
        results = d.get('results', [])
        return results, 'ok'
        
    except Exception as e:
        return [], str(e)

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 获取无电话的创新型中小企业
    print("=" * 60)
    print("【创新型中小企业电话补抓】")
    print("=" * 60)
    
    c.execute("""
        SELECT id, name, district 
        FROM customers 
        WHERE industry LIKE '%创新型%' 
        AND (phone IS NULL OR phone = '' OR phone = '无')
        LIMIT 500
    """)
    no_phone = c.fetchall()
    print(f"需补抓电话: {len(no_phone)}家")
    
    # 按区县分组
    district_groups = {}
    for row in no_phone:
        dist = row[2] if row[2] else '其他'
        if dist not in district_groups:
            district_groups[dist] = []
        district_groups[dist].append(row)
    
    print(f"\n按区县分布:")
    for dist, items in sorted(district_groups.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"  {dist}: {len(items)}家")
    
    # 开始补抓
    updated = 0
    skipped = 0
    errors = 0
    
    for district, items in list(district_groups.items())[:5]:  # 先处理前5个区县
        print(f"\n【{district}】开始补抓 {len(items)}家...")
        
        center = DISTRICTS.get(district, {'lat': 29.563, 'lng': 106.551})
        
        # 关键词
        keywords = ['科技有限公司', '机械有限公司', '建材有限公司', '食品有限公司', 
                    '实业有限公司', '贸易有限公司', '工贸有限公司', '新能源科技']
        
        for kw in keywords:
            if len(items) == 0:
                break
            
            for page in range(3):  # 每关键词最多3页
                if len(items) == 0:
                    break
                
                results, info = fetch_baidu_poi(kw, district=district, center=center, page=page)
                
                if info != 'ok':
                    print(f"  搜索'{kw}'第{page+1}页失败: {info}")
                    break
                
                for item in results:
                    if not items:
                        break
                    
                    name = item.get('name', '').strip()
                    tel = item.get('tel', '') or item.get('telephone', '') or ''
                    addr = item.get('address', '')
                    area = item.get('area', '')
                    
                    # 尝试匹配
                    for item_id, item_name, item_dist in items[:]:
                        # 简单匹配: 包含关键词
                        if kw.replace('公司', '') in name or kw.replace('公司', '') in item_name:
                            c.execute("""
                                UPDATE customers 
                                SET phone = ?, address = COALESCE(address, ?), 
                                    source = CONCAT(COALESCE(source, ''), '+百度POI补抓'),
                                    updated_at = ?
                                WHERE id = ?
                            """, (tel, addr, datetime.now().strftime('%Y-%m-%d %H:%M'), item_id))
                            
                            if c.rowcount > 0:
                                updated += 1
                                items.pop(0)
                                print(f"  ✓ {item_name} -> {tel[:10]}..." if tel else f"  ✗ {item_name} -> 无电话")
                            break
                
                time.sleep(0.5)
        
        # 保存进度
        progress = {
            'district': district,
            'total': len(district_groups[district]),
            'updated': len(district_groups[district]) - len(items),
            'remaining': len(items),
            'timestamp': datetime.now().isoformat()
        }
        progress_path = os.path.join(OUT_DIR, f'innovative_{district}_progress.json')
        with open(progress_path, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"补抓完成:")
    print(f"  更新电话: {updated}家")
    print(f"  无电话: {skipped}家")
    print(f"  错误: {errors}家")

if __name__ == '__main__':
    main()