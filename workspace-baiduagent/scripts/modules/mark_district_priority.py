# -*- coding: utf-8 -*-
"""
标注区域优先级
将机械行业企业按区域划分优先级
"""
import sys, sqlite3, json
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/baidu_crm.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print('='*70)
print('[District Priority Marking]')
print('='*70)
print(f'Execution time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('='*70)

# Define district priorities
DISTRICT_PRIORITY = {
    'P0': ['渝中区', '江北区', '南岸区', '九龙坡区', '沙坪坝区', 
           '渝北区', '大渡口区', '北碚区', '巴南区', '重庆高新区', '两江新区'],
    'P1': ['璧山区', '江津区', '合川区', '永川区', '大足区', '铜梁区'],
    'P2': ['綦江区', '南川区', '长寿区', '荣昌区', '双桥区'],
    'P3': ['开州区', '万州区', '涪陵区', '黔江区', '其他区县']
}

# Get all mechanical industry customers
print('\n[Step 1] Fetching mechanical industry customers...')
c.execute('''
    SELECT id, name, phone, district, address, industry
    FROM customers
    WHERE industry LIKE '%机械%' OR industry = '液压设备' 
       OR industry = '工程机械' OR industry = '数控机床'
       OR industry = '精密机械' OR industry = '自动化设备'
''')
rows = c.fetchall()
print(f'  Total: {len(rows)}')

# Mark priority
print('\n[Step 2] Marking district priority...')
priority_stats = {'P0': 0, 'P1': 0, 'P2': 0, 'P3': 0, 'Unknown': 0}
updates = []

for row in rows:
    district = row['district']
    
    # Determine priority
    if not district or district.strip() == '':
        priority = 'Unknown'
    elif district in DISTRICT_PRIORITY['P0']:
        priority = 'P0'
    elif district in DISTRICT_PRIORITY['P1']:
        priority = 'P1'
    elif district in DISTRICT_PRIORITY['P2']:
        priority = 'P2'
    else:
        priority = 'P3'
    
    priority_stats[priority] += 1
    updates.append({
        'id': row['id'],
        'name': row['name'],
        'district': district,
        'priority': priority,
        'phone': row['phone']
    })

# Save updates
output_file = f'data/source/district_priority_{datetime.now().strftime("%Y%m%d")}.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(updates, f, ensure_ascii=False, indent=2)
print(f'  Updates saved: {output_file}')

# Update database - add priority column if not exists
print('\n[Step 3] Updating database...')
try:
    c.execute('ALTER TABLE customers ADD COLUMN district_priority TEXT')
    print('  Added district_priority column')
except sqlite3.OperationalError:
    print('  Column already exists')

for u in updates:
    c.execute('UPDATE customers SET district_priority = ? WHERE id = ?', 
              (u['priority'], u['id']))

conn.commit()
print(f'  Updated {len(updates)} records')

# Statistics
print('\n' + '='*70)
print('[Priority Statistics]')
print('='*70)
print(f'{"Priority":<12} {"Count":<10} {"Percentage":<12} {"Status"}')
print('-'*60)
for p in ['P0', 'P1', 'P2', 'P3', 'Unknown']:
    count = priority_stats[p]
    pct = count / len(rows) * 100
    status = '✅' if p == 'P0' else ('⚠️' if p == 'Unknown' else '📍')
    print(f'{p:<12} {count:<10} {pct:>6.1f}%   {status}')
print('-'*60)
print(f'{"TOTAL":<12} {len(rows):<10} {100.0:>6.1f}%')

# Show samples by priority
print('\n' + '='*70)
print('[Sample Enterprises by Priority]')
print('='*70)

for priority in ['P0', 'P1', 'P2', 'Unknown']:
    print(f'\n{priority}:')
    samples = [u for u in updates if u['priority'] == priority and u['phone']]
    for s in samples[:5]:
        print(f'  - {s["name"][:35]}... | {s["district"] or "N/A"} | {s["phone"][:15]}...')

# Phone coverage by priority
print('\n' + '='*70)
print('[Phone Coverage by Priority]')
print('='*70)
print(f'{"Priority":<12} {"Total":<10} {"With Phone":<12} {"Rate":<10}')
print('-'*50)
for p in ['P0', 'P1', 'P2', 'P3', 'Unknown']:
    total = priority_stats[p]
    with_phone = sum(1 for u in updates if u['priority'] == p and u['phone'])
    rate = with_phone / total * 100 if total > 0 else 0
    print(f'{p:<12} {total:<10} {with_phone:<12} {rate:>6.1f}%')

conn.close()

print('\n' + '='*70)
print('[Priority Marking Complete]')
print('='*70)
