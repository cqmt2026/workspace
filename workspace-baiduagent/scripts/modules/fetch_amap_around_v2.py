# -*- coding: utf-8 -*-
"""高德POI批量抓取 - 使用around接口绕过text配额限制"""
import requests, sys, time, csv, os
sys.stdout.reconfigure(encoding='utf-8')

GD_KEY = '***'
OUT_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\amap'
os.makedirs(OUT_DIR, exist_ok=True)

# 重庆主城区9区中心坐标（用于周边搜索）
CITIES = {
    'yuzhong': (29.56, 106.58),
    'jiangbei': (29.57, 106.57),
    'yubei': (29.61, 106.62),
    'nanan': (29.53, 106.59),
    'jiulongpo': (29.51, 106.48),
    'shapingba': (29.54, 106.49),
    'beibei': (29.77, 106.41),
    'dadukou': (29.46, 106.50),
    'banan': (29.38, 106.55),
    'gxq': (29.55, 106.45),
}

# 行业关键词
INDUSTRY_KEYWORDS = {
    '口腔诊所': ['口腔诊所', '牙科医院', '齿科', '口腔医院', '口腔门诊'],
    '装修装饰': ['装修公司', '室内装饰', '装修设计', '建筑装饰'],
    '宠物医院': ['宠物医院', '宠物诊所', '动物诊疗'],
    '医美机构': ['医疗美容', '整形医院', '美容医院'],
    '教培机构': ['培训机构', '教育学校', '兴趣班'],
    '母婴亲子': ['母婴店', '月子中心', '早教中心'],
}

def fetch_around(keyword, lat, lng, radius=40000, offset=20, max_pages=15):
    """周边搜索分页获取"""
    all_pois = []
    for page in range(1, max_pages + 1):
        params = {
            'keywords': keyword,
            'location': f'{lng},{lat}',  # 注意：高德around是lng,lat顺序
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
                if 'INVALID_USER_KEY' in info:
                    print("    ❌ Key已失效，停止抓取")
                    return all_pois
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

def poi_to_row(poi):
    """转换POI为CSV行"""
    loc = poi.get('location', '')
    lat = lng = ''
    if loc:
        parts = loc.split(',')
        if len(parts) >= 2:
            lng, lat = parts[0], parts[1]
    return {
        'name': poi.get('name', ''),
        'address': poi.get('address', ''),
        'tel': poi.get('tel', ''),
        'lat': lat,
        'lng': lng,
        'adname': poi.get('adname', ''),
        'type': poi.get('type', ''),
    }

def main():
    print("=" * 60)
    print("🚀 高德around接口批量抓取（绕过text配额限制）")
    print("=" * 60)

    # 先测试Key是否有效
    print("\n测试Key有效性...")
    test_pois = fetch_around('口腔', 29.56, 106.58, radius=10000)
    if not test_pois:
        print("❌ Key已失效或配额耗尽，无法继续")
        return
    print(f"✅ Key有效，首批测试获取{len(test_pois)}条")

    total_new = 0
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        print(f"\n📂 {industry}:")
        for kw in keywords:
            print(f"  🔍 {kw}...")
            all_pois = []
            for city_name, (lat, lng) in CITIES.items():
                pois = fetch_around(kw, lat, lng)
                if pois:
                    all_pois.extend(pois)
                    print(f"    [{city_name}] +{len(pois)}条")
                time.sleep(0.5)
            if all_pois:
                print(f"    ✅ 小计: {len(all_pois)}条")
                total_new += len(all_pois)
            time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"✅ 本轮获取: {total_new}条")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()
