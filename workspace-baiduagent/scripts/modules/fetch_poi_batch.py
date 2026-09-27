# -*- coding: utf-8 -*-
"""高德POI批量抓取工具 - 支持续跑和断点"""
import requests, sys, time, csv, os
sys.stdout.reconfigure(encoding='utf-8')

GD_KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
OUT_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\amap'
MASTER_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'

# 行业关键词配置
INDUSTRY_KEYWORDS = {
    '口腔诊所': ['口腔诊所', '牙科医院', '齿科', '口腔医院', '口腔门诊'],
    '装修装饰': ['装修公司', '室内装饰', '装修工程', '建筑装饰', '装修设计'],
    '教培机构': ['培训机构', '教育学校', '兴趣班', '补习班', '艺术培训', '体育培训'],
    '宠物医院': ['宠物医院', '宠物诊所', '动物诊疗', '宠物保健'],
    '医美机构': ['医疗美容', '医美', '整形医院', '美容医院', '整形门诊'],
    '母婴亲子': ['母婴店', '月子中心', '早教中心', '儿童乐园', '孕婴'],
    '机械装备汽配': ['机械厂', '机械制造', '汽配', '汽车零部件', '机械设备'],
    '新材料化工': ['新材料', '化工', '化工厂', '涂料', '新材料科技'],
    '医疗器械': ['医疗器械', '医疗设备', '医药器械', '生物科技'],
    '环保检测': ['环保检测', '环境监测', '检测服务', '质检'],
    '建筑建材': ['建筑材料', '建材', '水泥', '钢材', '防水材料'],
    '新能源充电电力': ['充电桩', '新能源', '光伏发电', '电力工程', '变电所'],
}

def fetch_poi(keyword, city='重庆', offset=20, max_pages=50):
    """分页获取POI数据"""
    all_pois = []
    for page in range(1, max_pages + 1):
        params = {
            'keywords': keyword,
            'city': city,
            'offset': offset,
            'page': page,
            'key': GD_KEY,
            'types': ''  # 不限制类型
        }
        try:
            r = requests.get('https://restapi.amap.com/v3/place/text',
                params=params, timeout=10)
            d = r.json()
            if d.get('status') != '1':
                info = d.get('info', '')
                if 'OVER_LIMIT' in info or 'quota' in info.lower():
                    print(f"    ⚠️ 配额超限，等待30秒后继续...")
                    time.sleep(30)
                    continue
                else:
                    print(f"    ❌ API错误: {info}")
                    break
            pois = d.get('pois', [])
            if not pois:
                break
            all_pois.extend(pois)
            print(f"    page{page}: +{len(pois)}条 (累计{len(all_pois)})")
            if len(pois) < offset:
                break
            time.sleep(0.3)  # 限流
        except Exception as e:
            print(f"    ❌ 请求异常: {e}")
            time.sleep(5)
            continue
    return all_pois

def poi_to_row(poi):
    """转换POI为CSV行"""
    return {
        'name': poi.get('name', ''),
        'address': poi.get('address', ''),
        'tel': poi.get('tel', ''),
        'location': poi.get('location', ''),
        'adname': poi.get('adname', ''),
        'cityname': poi.get('cityname', ''),
        'type': poi.get('type', ''),
        'typecode': poi.get('typecode', ''),
        'biz_ext': poi.get('biz_ext', ''),
    }

def save_poi(pois, industry, keyword):
    """保存并去重"""
    fname = f"{industry}_{keyword.replace('/', '_')}.csv"
    fpath = os.path.join(OUT_DIR, fname)
    
    existing = set()
    if os.path.exists(fpath):
        with open(fpath, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing.add(row['name'])
    
    new_pois = [p for p in pois if p['name'] not in existing]
    all_pois = list(existing.union(set(p['name'] for p in new_pois)))  # Keep all
    
    with open(fpath, 'w', encoding='utf-8-sig', newline='') as f:
        if new_pois:
            writer = csv.DictWriter(f, fieldnames=['name','address','tel','location','adname','cityname','type'])
            writer.writeheader()
            for poi in new_pois:
                writer.writerow(poi_to_row(poi))
    
    return len(new_pois)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    
    print("=" * 60)
    print("🚀 高德POI批量抓取工具")
    print("=" * 60)
    
    total_new = 0
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        print(f"\n📂 {industry}:")
        for kw in keywords:
            print(f"  🔍 搜索: {kw}")
            pois = fetch_poi(kw)
            if pois:
                new_count = save_poi(pois, industry, kw)
                total_new += new_count
                print(f"     ✅ +{new_count}条新数据")
            time.sleep(1)
    
    print(f"\n{'=' * 60}")
    print(f"✅ 本轮新增: {total_new}条")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()
