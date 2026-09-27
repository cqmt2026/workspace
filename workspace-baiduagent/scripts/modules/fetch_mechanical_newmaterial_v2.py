# -*- coding: utf-8 -*-
"""
百度POI补抓 - 机械设备 + 新材料行业（修正版）
"""
import sys
import requests
import json
import sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BD_KEY = '***'
conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()

def search(query, page=0):
    """搜索百度POI"""
    r = requests.get('https://api.map.baidu.com/place/v2/search', params={
        'query': query, 'region': '重庆', 'output': 'json', 'ak': BD_KEY,
        'page_size': 20, 'page_num': page, 'scope': 2, 'region_fix': 1
    }, timeout=10).json()
    return r.get('results', []) if r.get('status') == 0 else []

def parse_poi(poi, industry):
    """解析POI结果"""
    loc = poi.get('location', {})
    return {
        'name': poi.get('name', ''),
        'phone': poi.get('telephone', ''),
        'address': poi.get('address', ''),
        'district': poi.get('area', ''),
        'industry': industry,
        'lng': loc.get('lng', ''),
        'lat': loc.get('lat', ''),
        'source': '百度POI补抓'
    }

all_results = []
seen = set()

# 搜索机械设备
print('搜索机械设备...')
mech_count = 0
for kw in ['重庆机械设备', '重庆机械制造', '重庆金属加工', '重庆精密机械']:
    for page in range(5):
        pois = search(kw, page)
        if not pois:
            break
        for poi in pois:
            p = parse_poi(poi, '机械装备汽配')
            if p['name'] not in seen:
                seen.add(p['name'])
                all_results.append(p)
                mech_count += 1
        print(f'  {kw} 第{page+1}页: {len(pois)}条 (新增{mech_count}条)')
        if len(pois) < 20:
            break

print(f'\n机械设备共: {mech_count}条')

# 搜索新材料
print('\n搜索新材料...')
nm_count = 0
for kw in ['重庆新材料', '重庆化工材料', '重庆复合材料', '重庆塑胶材料']:
    for page in range(5):
        pois = search(kw, page)
        if not pois:
            break
        for poi in pois:
            p = parse_poi(poi, '新材料化工')
            if p['name'] not in seen:
                seen.add(p['name'])
                all_results.append(p)
                nm_count += 1
        print(f'  {kw} 第{page+1}页: {len(pois)}条 (新增{nm_count}条)')
        if len(pois) < 20:
            break

print(f'\n新材料共: {nm_count}条')

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

print(f'\n=== 补抓汇总 ===')
print(f'总抓取数: {len(all_results)}')
print(f'有电话数: {sum(1 for r in all_results if r["phone"])}')
print(f'有坐标数: {sum(1 for r in all_results if r["lat"] and r["lng"])}')
print(f'有区域数: {sum(1 for r in all_results if r["district"])}')
print(f'新增入库: {inserted}条')
print(f'更新已有: {updated}条')

# 保存详细数据
output_file = f'data/source/baidu_poi_机械新材料_{datetime.now().strftime("%Y%m%d")}.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
print(f'\n💾 详细数据已保存: {output_file}')
