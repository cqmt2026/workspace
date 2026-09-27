# -*- coding: utf-8 -*-
"""高德周边搜索批量抓取 - 绕过天配额限制"""
import requests, sys, time, csv, os
sys.stdout.reconfigure(encoding='utf-8')

GD_KEY = '3f85cf…bd51'
OUT_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\amap'
os.makedirs(OUT_DIR, exist_ok=True)

# 重庆主城区9区中心坐标
CITIES = {
    'yuzhong': (106.58, 29.56),
    'jiangbei': (106.57, 29.57),
    'yubei': (106.62, 29.61),
    'nanan': (106.59, 29.53),
    'jiulongpo': (106.48, 29.51),
    'shapingba': (106.49, 29.54),
    'beibei': (106.41, 29.77),
    'dadukou': (106.50, 29.46),
    'banan': (106.55, 29.38),
    'gxq': (106.45, 29.55),  # 高新区
}

# 行业关键词
INDUSTRIES = {
    '口腔诊所': ['口腔诊所', '牙科医院', '齿科', '口腔医院'],
    '装修装饰': ['装修公司', '室内装饰', '装修设计', '建筑装饰'],
    '宠物医院': ['宠物医院', '宠物诊所', '动物诊疗'],
    '医美机构': ['医疗美容', '整形医院', '美容医院'],
    '教培机构': ['培训机构', '教育学校', '兴趣班'],
    '母婴亲子': ['母婴店', '月子中心', '早教中心'],
}

def fetch_around(keyword, lat, lng, radius=30000, offset=20, max_pages=10):
    """周边搜索分页获取"""
    all_pois = []
    for page in range(1, max_pages + 1):
        params = {
            'keywords': keyword,
            'location': f'{lng},{lat}',
            'radius': radius,
            'offset': offset,
            'page': page,
            'key': GD_KEY,
        }
        try:
            r = requests.get('https://restapi.amap.com/v3/place/around',
                params=params, timeout=10)
            d = r.json()
            if d.get('status') != '1':
                info = d.get('info', '')
                print(f"    ⚠️ {info}")
                break
            pois = d.get('pois', [])
            if not pois:
                break
            all_pois.extend(pois)
            if len(pois) < offset:
                break
            time.sleep(0.3)
        except Exception as e:
            print(f"    ❌ {e}")
            time.sleep(3)
    return all_pois

def main():
    total = 0
    for industry, keywords in INDUSTRIES.items():
        print(f"\n📂 {industry}:")
        for city_name, (lat, lng) in CITIES.items():
            for kw in keywords:
                pois = fetch_around(kw, lat, lng)
                if pois:
                    print(f"  [{city_name}] {kw}: +{len(pois)}条")
                    total += len(pois)
                time.sleep(0.5)
    
    print(f"\n{'='*40}")
    print(f"✅ 本轮获取: {total}条（去重前）")
    print(f"{'='*40}")

if __name__ == '__main__':
    main()
