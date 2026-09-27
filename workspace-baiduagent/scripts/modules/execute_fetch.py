# -*- coding: utf-8 -*-
import sys, requests, json, sqlite3
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

BD_KEY = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()

print('='*60)
print('[Baidu POI Fetch - Mechanical & New Materials]')
print('='*60)

# Search mechanical equipment
print('\n[1] Searching mechanical equipment...')
pois_mech = []
for page in range(5):
    r = requests.get('https://api.map.baidu.com/place/v2/search', params={
        'query': 'Chongqing Mechanical Equipment',
        'region': 'Chongqing',
        'output': 'json',
        'ak': BD_KEY,
        'page_size': 20,
        'page_num': page,
        'scope': 2
    }, timeout=10).json()
    if r.get('status') == 0:
        results = r.get('results', [])
        pois_mech.extend(results)
        print(f'    Page {page+1}: {len(results)} records (total {len(pois_mech)})')
        if len(results) < 20:
            break
    else:
        print(f'    API error: {r.get("message")}')
        break

print(f'    Mechanical total: {len(pois_mech)} records')

# Search new materials
print('\n[2] Searching new materials...')
pois_nm = []
for page in range(5):
    r = requests.get('https://api.map.baidu.com/place/v2/search', params={
        'query': 'Chongqing New Materials',
        'region': 'Chongqing',
        'output': 'json',
        'ak': BD_KEY,
        'page_size': 20,
        'page_num': page,
        'scope': 2
    }, timeout=10).json()
    if r.get('status') == 0:
        results = r.get('results', [])
        pois_nm.extend(results)
        print(f'    Page {page+1}: {len(results)} records (total {len(pois_nm)})')
        if len(results) < 20:
            break
    else:
        print(f'    API error: {r.get("message")}')
        break

print(f'    New materials total: {len(pois_nm)} records')

# Process data
all_results = []
seen = set()

for poi in pois_mech:
    name = poi.get('name', '')
    if name not in seen:
        seen.add(name)
        all_results.append({
            'name': name,
            'phone': poi.get('telephone', ''),
            'address': poi.get('address', ''),
            'district': poi.get('area', ''),
            'industry': 'Mechanical Equipment',
            'lng': poi.get('location', {}).get('lng', ''),
            'lat': poi.get('location', {}).get('lat', ''),
            'source': 'Baidu POI Fetch'
        })

for poi in pois_nm:
    name = poi.get('name', '')
    if name not in seen:
        seen.add(name)
        all_results.append({
            'name': name,
            'phone': poi.get('telephone', ''),
            'address': poi.get('address', ''),
            'district': poi.get('area', ''),
            'industry': 'New Materials',
            'lng': poi.get('location', {}).get('lng', ''),
            'lat': poi.get('location', {}).get('lat', ''),
            'source': 'Baidu POI Fetch'
        })

print(f'\n[3] After deduplication: {len(all_results)} records')

# Save to database
print('\n[4] Saving to database...')
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

print()
print('='*60)
print('[Fetch Summary]')
print('='*60)
print(f'Total fetched: {len(all_results)}')
print(f'With phone: {sum(1 for r in all_results if r["phone"])}')
print(f'With coordinates: {sum(1 for r in all_results if r["lat"] and r["lng"])}')
print(f'With district: {sum(1 for r in all_results if r["district"])}')
print(f'New records: {inserted}')
print(f'Updated records: {updated}')

# Save detailed data
output_file = f'data/source/baidu_poi_mech_newmat_{datetime.now().strftime("%Y%m%d")}.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
print(f'\nDetailed data saved: {output_file}')
