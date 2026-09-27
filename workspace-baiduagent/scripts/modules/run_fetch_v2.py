# -*- coding: utf-8 -*-
import sys, requests, json, sqlite3
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

BD_KEY = '***'
conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()

def search(q, page=0):
    r = requests.get('https://api.map.baidu.com/place/v2/search', params={
        'query': q, 'region': '重庆', 'output': 'json', 'ak': BD_KEY,
        'page_size': 20, 'page_num': page, 'scope': 2, 'region_fix': 1
    }, timeout=10).json()
    if r.get('status') == 0:
        return r.get('results', [])
    return []

all_results = []
seen_names = set()

print('='*60)
print('【百度POI补抓 - 机械设备 + 新材料】')
print('='*60)

# 搜索机械设备
print('\n搜索机械设备...')
mech_results = []
for kw in ['重庆机械设备', '重庆机械制造', '重庆金属加工', '重庆精密机械', '重庆数控机床']:
    for page in range(5):
        pois = search(kw, page)
        if not pois:
            break
        for poi in pois:
            name = poi.get('name', '')
            if name not in seen_names:
                seen_names.add(name)
                mech_results.append({
                    'name': name,
                    'phone': poi.get('telephone', ''),
                    'address': poi.get('address', ''),
                    'district': poi.get('area', ''),
                    'industry': '机械装备汽配',
                    'lng': poi.get('location', {}).get('lng', ''),
                    'lat': poi.get('location', {}).get('lat', ''),
                    'source': '百度POI补抓'
                })
        print(f'  {kw} 第{page+1}页: {len(pois)}条')
        if len(pois) < 20:
            break

print(f'机械设备共: {len(mech_results)}条')
all_results.extend(mech_results)

# 搜索新材料
print('\n搜索新材料...')
nm_results = []
for kw in ['重庆新材料', '重庆化工材料', '重庆复合材料', '重庆塑胶材料', '重庆建筑材料']:
    for page in range(5):
        pois = search(kw, page)
        if not pois:
            break
        for poi in pois:
            name = poi.get('name', '')
            if name not in seen_names:
                seen_names.add(name)
                nm_results.append({
                    'name': name,
                    'phone': poi.get('telephone', ''),
                    'address': poi.get('address', ''),
                    'district': poi.get('area', ''),
                    'industry': '新材料化工',
                    'lng': poi.get('location', {}).get('lng', ''),
                    'lat': poi.get('location', {}).get('lat', ''),
                    'source': '百度POI补抓'
                })
        print(f'  {kw} 第{page+1}页: {len(pois)}条')
        if len(pois) < 20:
            break

print(f'新材料共: {len(nm_results)}条')
all_results.extend(nm_results)

# 保存到数据库
print('\n保存到数据库...')
inserted = updated = 0
for r in all_results:
    c.execute('SELECT id FROM customers WHERE name = ?', (r['name'],))
    existing = c.fetchone()
    if existing:
        c.execute('UPDATE customers SET phone=?, district=?, lat=?, lng=?, source=?, updated_at=? WHERE id=?',
            (r['phone'], r['district'], r['lat'], r['lng'], r['source'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), existing[0]))
        updated += 1
    else:
        c.execute('INSERT INTO customers (name, industry, tier, phone, contact, source, status, address, district, lat, lng, note, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (r['name'], r['industry'], '', r['phone'], '', r['source'], '待联系', r['address'], r['district'], r['lat'], r['lng'], '', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        inserted += 1

conn.commit()
conn.close()

print()
print('='*60)
print('【补抓汇总】')
print('='*60)
print(f'总抓取数: {len(all_results)}')
phone_count = sum(1 for r in all_results if r['phone'])
coord_count = sum(1 for r in all_results if r['lat'] and r['lng'])
dist_count = sum(1 for r in all_results if r['district'])
print(f'有电话数: {phone_count}')
print(f'有坐标数: {coord_count}')
print(f'有区域数: {dist_count}')
print(f'新增入库: {inserted}条')
print(f'更新已有: {updated}条')

# 保存详细数据
output_file = f'data/source/baidu_poi_机械新材料_{datetime.now().strftime("%Y%m%d")}.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
print(f'详细数据已保存: {output_file}')
