# -*- coding: utf-8 -*-
"""
机械行业彻底补抓脚本
覆盖所有机械相关子行业
"""
import sys, requests, json, sqlite3
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

BD_KEY = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()

print('='*70)
print('[Mechanical Industry Complete Fetch]')
print('='*70)
print(f'Execution time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('='*70)

# Mechanical industry keywords (comprehensive)
MECH_KEYWORDS = [
    '重庆机械设备',
    '重庆机械制造',
    '重庆金属加工',
    '重庆精密机械',
    '重庆数控机床',
    '重庆注塑机',
    '重庆机床',
    '重庆工程机械',
    '重庆液压设备',
    '重庆气动设备',
    '重庆传动设备',
    '重庆轴承',
    '重庆齿轮',
    '重庆焊接设备',
    '重庆切割设备',
    '重庆铸造',
    '重庆锻造',
    '重庆钣金',
    '重庆模具',
    '重庆自动化设备',
    '重庆机器人',
    '重庆包装机械',
    '重庆食品机械',
    '重庆纺织机械',
    '重庆印刷机械',
    '重庆化工设备',
    '重庆环保设备',
    '重庆锅炉',
    '重庆阀门',
    '重庆泵',
    '重庆压缩机',
    '重庆风机',
    '重庆减速器',
    '重庆电机',
    '重庆电气',
    '重庆仪器仪表',
    '重庆量具',
    '重庆刃具',
    '重庆工具',
    '重庆汽配件',
    '重庆汽车配件',
    '重庆摩托车配件',
    '重庆五金工具',
    '重庆标准件',
    '重庆紧固件',
    '重庆轴承供应',
    '重庆润滑油',
    '重庆润滑油供应',
]

all_results = []
seen_names = set()
total_calls = 0

# Fetch data for each keyword
print('\n[Phase 1] Fetching mechanical industry data...')
print('-'*70)

for kw in MECH_KEYWORDS:
    print(f'\nSearching: {kw}')
    kw_results = []
    
    for page in range(10):  # Max 10 pages per keyword
        total_calls += 1
        r = requests.get('https://api.map.baidu.com/place/v2/search', params={
            'query': kw,
            'region': 'Chongqing',
            'output': 'json',
            'ak': BD_KEY,
            'page_size': 20,
            'page_num': page,
            'scope': 2
        }, timeout=10).json()
        
        if r.get('status') != 0:
            print(f'  API error: {r.get("message")}')
            break
        
        results = r.get('results', [])
        if not results:
            break
        
        for poi in results:
            name = poi.get('name', '')
            if name not in seen_names:
                seen_names.add(name)
                kw_results.append({
                    'name': name,
                    'phone': poi.get('telephone', ''),
                    'address': poi.get('address', ''),
                    'district': poi.get('area', ''),
                    'industry': '机械装备汽配',
                    'lng': poi.get('location', {}).get('lng', ''),
                    'lat': poi.get('location', {}).get('lat', ''),
                    'source': 'Baidu POI Complete Fetch'
                })
        
        print(f'  Page {page+1}: {len(results)} records (new: {len([r for r in results if r.get("name", "") not in seen_names])})')
        
        if len(results) < 20:
            break
    
    all_results.extend(kw_results)
    print(f'  Subtotal: {len(kw_results)} new records')
    
    # Stop if we have enough data
    if len(all_results) >= 500:
        print(f'\nTarget reached: {len(all_results)} records')
        break

print(f'\n[Phase 1 Complete] Total fetched: {len(all_results)} records')
print(f'Total API calls: {total_calls}')

# Save to database
print('\n[Phase 2] Saving to database...')
print('-'*70)

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
            (r['name'], r['industry'], '', r['phone'], '', r['source'], 'pending', r['address'], r['district'], r['lat'], r['lng'], '', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        inserted += 1

conn.commit()
conn.close()

# Summary
print('\n' + '='*70)
print('[Fetch Summary]')
print('='*70)
print(f'Total fetched: {len(all_results)}')
print(f'With phone: {sum(1 for r in all_results if r["phone"])}')
print(f'With coordinates: {sum(1 for r in all_results if r["lat"] and r["lng"])}')
print(f'With district: {sum(1 for r in all_results if r["district"])}')
print(f'New records: {inserted}')
print(f'Updated records: {updated}')
print(f'Total API calls: {total_calls}')

# Save detailed data
output_file = f'data/source/baidu_poi_mechanical_complete_{datetime.now().strftime("%Y%m%d")}.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
print(f'\nDetailed data saved: {output_file}')

print('\n' + '='*70)
print('[Fetch Complete]')
print('='*70)
