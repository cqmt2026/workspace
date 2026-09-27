# -*- coding: utf-8 -*-
"""腾讯地图POI批量抓取工具
注意：Key从环境变量读取，避免明文硬编码
"""
import requests, sys, time, csv, os
sys.stdout.reconfigure(encoding='utf-8')

TX_KEY = os.environ.get('TX_MAP_KEY', '')
if not TX_KEY:
    print('❌ 未配置TX_MAP_KEY环境变量')
    sys.exit(1)

OUT_DIR = r'data\source\tencent'
MASTER_DIR = r'data\master'
os.makedirs(OUT_DIR, exist_ok=True)

INDUSTRY_KEYWORDS = {
    '人力资源': ['人力资源公司','劳务派遣','猎头公司','人才市场','企业管理咨询'],
    '软件信息': ['软件公司','软件开发','软件研发','IT服务','信息系统'],
    '物流货运': ['物流公司','货运公司','物流园','仓储物流','快递公司'],
    '检验检测': ['检测公司','质检','质量检测','检测机构'],
    '智能制造': ['智能制造','智能装备','工业机器人','自动化设备'],
}

def fetch_tencent(keyword, max_pages=20):
    all_pois = []
    for page in range(1, max_pages + 1):
        params = {'key': TX_KEY, 'boundary': 'region(重庆,0)', 'keyword': keyword, 'max_per_page': 20, 'page': page}
        try:
            r = requests.get('https://apis.map.qq.com/ws/place/v1/search', params=params, timeout=10)
            d = r.json()
            if d.get('status') != 0:
                msg = d.get('message', '')
                if 'quota' in msg.lower() or 'limit' in msg.lower():
                    print(f"    ⚠️ 配额超限")
                    break
                else:
                    print(f"    ❌ API错误: {msg}")
                    break
            data = d.get('data', [])
            if not data: break
            all_pois.extend(data)
            print(f"    page{page}: +{len(data)}条 (累计{len(all_pois)})")
            if len(data) < 20: break
            time.sleep(0.3)
        except Exception as e:
            print(f"    ❌ 异常: {e}")
            time.sleep(3)
    return all_pois

def poi_to_row(poi):
    loc = poi.get('location', {})
    return {'name': poi.get('title', ''), 'address': poi.get('address', ''), 'tel': poi.get('tel', ''), 'lat': loc.get('lat', ''), 'lng': loc.get('lng', ''), 'category': poi.get('category', ''), 'ad_info': poi.get('ad_info', '')}

def save_poi(pois, industry, keyword):
    fname = f"{industry}_{keyword.replace('/', '_')}.csv"
    fpath = os.path.join(OUT_DIR, fname)
    existing_names = set()
    if os.path.exists(fpath):
        with open(fpath, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader: existing_names.add(row['name'])
    new_pois = [p for p in pois if p.get('title', '') not in existing_names]
    if new_pois:
        with open(fpath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['name','address','tel','lat','lng','category','ad_info'])
            writer.writeheader()
            for poi in new_pois: writer.writerow(poi_to_row(poi))
    return len(new_pois)

def main():
    print("="*60)
    print("【腾讯地图POI批量抓取】Key: 环境变量 TX_MAP_KEY")
    print("="*60)
    total_new = total_fetched = 0
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        print(f"\n📂 {industry}:")
        for kw in keywords:
            print(f"  🔍 {kw}...")
            pois = fetch_tencent(kw)
            if pois:
                new_count = save_poi(pois, industry, kw)
                total_new += new_count
                total_fetched += len(pois)
                print(f"     ✅ +{new_count}条 (总{len(pois)}条)")
            time.sleep(0.5)
    print(f"\n{'='*60}")
    print(f"✅ 本次抓取: {total_fetched}条")
    print(f"✅ 新增数据: {total_new}条")

if __name__ == '__main__':
    main()