# -*- coding: utf-8 -*-
"""高德物业服务补抓"""
import sys, requests, time, csv
sys.stdout.reconfigure(encoding='utf-8')

GD = '3f85cf676f4eb0ccb2374560bb99bd51'
BASE = 'https://restapi.amap.com/v3/place/text'
districts = ['渝中','江北','南岸','九龙坡','沙坪坝','北碚','大渡口','巴南','高新','两江']

all_items = []
seen = set()

for kw in ['物业服务','物业公司','物业管理']:
    for page in range(1, 15):
        r = requests.get(BASE, params={
            'key': GD, 'keywords': kw,
            'city': '重庆', 'offset': 50, 'page': page, 'extensions': 'all'
        }, timeout=15).json()
        if r.get('status') != '1' or r.get('info') != 'OK':
            print(f'  {kw} p{page}: status={r.get("status")}, info={r.get("info")} - 停止')
            break
        pois = r.get('pois', [])
        if not pois:
            break
        new_count = 0
        for p in pois:
            name = p.get('name', '').strip()
            if not name or name in seen:
                continue
            area = p.get('adname', '')
            if not any(d in area for d in districts):
                continue
            tel = (p.get('tel') or '').replace(';', ',').replace('；', ',')
            loc = p.get('entr_location') or p.get('location', '')
            lng, lat = '', ''
            if loc:
                parts = loc.split(',')
                if len(parts) >= 2:
                    lng, lat = parts[0], parts[1]
            seen.add(name)
            all_items.append({
                '区域': area, '机构名称': name, '地址': p.get('address', ''),
                '电话': tel, '经度': lng, '纬度': lat
            })
            new_count += 1
        print(f'  {kw} p{page}: +{new_count} (累计{len(all_items)})')
        if new_count == 0:
            break

print(f'\n物业去重后: {len(all_items)}条, 有电话: {sum(1 for i in all_items if i["电话"])}家')

# 保存
out = 'data/master/物业服务_gaode_20260903.csv'
fieldnames = ['区域', '机构名称', '地址', '电话', '经度', '纬度', '数据来源', '抓取时间']
with open(out, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for item in all_items:
        w.writerow({**item, '数据来源': '高德地图POI', '抓取时间': time.strftime('%Y-%m-%d %H:%M')})
print(f'已保存: {out}')
