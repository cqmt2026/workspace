# -*- coding: utf-8 -*-
"""
机械设备行业企业单独分类脚本
将机械装备汽配行业细分为更精准的子行业
"""
import sys, sqlite3, json
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/baidu_crm.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print('='*70)
print('[Mechanical Industry Classification]')
print('='*70)
print(f'Execution time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('='*70)

# Get all mechanical industry customers
print('\n[Step 1] Fetching mechanical industry customers...')
c.execute('''
    SELECT id, name, phone, address, district, industry, source, lat, lng
    FROM customers
    WHERE industry = '机械装备汽配'
''')
rows = c.fetchall()
print(f'  Total mechanical customers: {len(rows)}')

# Classification rules
def classify_mechanical(name, address, source):
    """Classify mechanical enterprise into sub-industry"""
    name = str(name).lower()
    address = str(address).lower() if address else ''
    
    # Heavy machinery
    if any(kw in name for kw in ['工程', '工程机械', '筑路', '铲车', '挖掘机', '起重机', '吊车', '泵车', '搅拌站', '压路机', '摊铺机']):
        return '工程机械'
    
    # CNC/Machine tools
    if any(kw in name for kw in ['数控', '机床', ' CNC', 'lathe', ' milling', 'grinding', '车床', '铣床', '磨床', '钻床', '加工中心']):
        return '数控机床'
    
    # Precision machinery
    if any(kw in name for kw in ['精密', '精机', '高精度', 'micro']):
        return '精密机械'
    
    # Injection molding
    if any(kw in name for kw in ['注塑', 'molding', '塑料机械', 'blowing']):
        return '注塑机械'
    
    # Hydraulic equipment
    if any(kw in name for kw in ['液压', 'hydraulic', '油缸', '泵站']):
        return '液压设备'
    
    # Pneumatic equipment
    if any(kw in name for kw in ['气动', 'pneumatic', '气阀', '气缸']):
        return '气动设备'
    
    # Transmission equipment
    if any(kw in name for kw in ['传动', 'transmission', '减速器', '减速机', 'gearbox']):
        return '传动设备'
    
    # Bearing
    if any(kw in name for kw in ['轴承', 'bearing', '轴承供应']):
        return '轴承'
    
    # Gear
    if any(kw in name for kw in ['齿轮', 'gear', '齿条']):
        return '齿轮'
    
    # Welding equipment
    if any(kw in name for kw in ['焊接', 'welding', '焊割', '焊机能']):
        return '焊接设备'
    
    # Cutting equipment
    if any(kw in name for kw in ['切割', 'cutting', '激光切割', '等离子', '水刀']):
        return '切割设备'
    
    # Casting
    if any(kw in name for kw in ['铸造', 'casting', '铸件', '铸铁']):
        return '铸造'
    
    # Forging
    if any(kw in name for kw in ['锻造', 'forging', '锻件', '锻钢']):
        return '锻造'
    
    # Sheet metal
    if any(kw in name for kw in ['钣金', 'sheet metal', '折弯', '冲压']):
        return '钣金加工'
    
    # Mold/Die
    if any(kw in name for kw in ['模具', 'mold', 'die', '冲压模', '注塑模']):
        return '模具'
    
    # Automation/Robot
    if any(kw in name for kw in ['自动化', 'robot', '机器人', '机械臂', 'automat']):
        return '自动化设备'
    
    # Packaging machinery
    if any(kw in name for kw in ['包装', 'packaging', '灌装', '封口']):
        return '包装机械'
    
    # Food machinery
    if any(kw in name for kw in ['食品机械', 'food machine', '烘焙', '饮料设备']):
        return '食品机械'
    
    # Textile machinery
    if any(kw in name for kw in ['纺织', 'textile', '织机', '印染']):
        return '纺织机械'
    
    # Printing machinery
    if any(kw in name for kw in ['印刷', 'printing', '印刷机', '印后']):
        return '印刷机械'
    
    # Chemical equipment
    if any(kw in name for kw in ['化工设备', 'chemical', '反应器', '储罐']):
        return '化工设备'
    
    # Environmental equipment
    if any(kw in name for kw in ['环保设备', 'environmental', '污水处理', '废气']):
        return '环保设备'
    
    # Boiler
    if any(kw in name for kw in ['锅炉', 'boiler', '蒸汽']):
        return '锅炉'
    
    # Valve
    if any(kw in name for kw in ['阀门', 'valve', '阀']):
        return '阀门'
    
    # Pump
    if any(kw in name for kw in ['泵', 'pump', '水泵', '油泵']):
        return '泵'
    
    # Compressor
    if any(kw in name for kw in ['压缩机', 'compressor', '空压']):
        return '压缩机'
    
    # Fan
    if any(kw in name for kw in ['风机', 'fan', '鼓风机', '通风']):
        return '风机'
    
    # Motor/Electric
    if any(kw in name for kw in ['电机', 'motor', '电气', 'electric', '配电']):
        return '电机电气'
    
    # Instrument/Measurement
    if any(kw in name for kw in ['仪表', 'instrument', '仪器', '测量', '量具']):
        return '仪器仪表'
    
    # Tool
    if any(kw in name for kw in ['刀具', 'tool', '刃具', '量具', '扳手', '螺丝刀']):
        return '五金工具'
    
    # Fastener/Standard part
    if any(kw in name for kw in ['标准件', '紧固件', 'fastener', '螺栓', '螺母', '螺丝']):
        return '标准件'
    
    # Lubricant
    if any(kw in name for kw in ['润滑油', 'lubricant', '液压油', '润滑脂']):
        return '润滑油'
    
    # Auto parts
    if any(kw in name for kw in ['汽配件', '汽车配件', 'auto part', '摩托车配件']):
        return '汽摩配件'
    
    # Metal processing
    if any(kw in name for kw in ['金属加工', 'metal', '切削', '车削', '铣削']):
        return '金属加工'
    
    # General machinery
    return '通用机械'

# Classify and update
print('\n[Step 2] Classifying mechanical enterprises...')
updates = []
for row in rows:
    sub_industry = classify_mechanical(row['name'], row['address'], row['source'])
    updates.append({
        'id': row['id'],
        'name': row['name'],
        'old_industry': row['industry'],
        'new_industry': sub_industry,
        'phone': row['phone']
    })

# Save classification results
output_file = f'data/source/mechanical_classification_{datetime.now().strftime("%Y%m%d")}.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(updates, f, ensure_ascii=False, indent=2)
print(f'  Classification results saved: {output_file}')

# Update database
print('\n[Step 3] Updating database...')
c.execute('BEGIN TRANSACTION')
for u in updates:
    c.execute('UPDATE customers SET industry = ? WHERE id = ?', (u['new_industry'], u['id']))
conn.commit()
print(f'  Updated {len(updates)} records')

# Statistics
print('\n' + '='*70)
print('[Classification Statistics]')
print('='*70)

c.execute('''
    SELECT industry, COUNT(*) as count,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone
    FROM customers
    WHERE industry LIKE '%机械%' OR industry LIKE '%精密%' OR industry LIKE '%数控%'
       OR industry = '工程机械' OR industry = '注塑机械' OR industry = '液压设备'
       OR industry = '气动设备' OR industry = '传动设备' OR industry = '轴承'
       OR industry = '齿轮' OR industry = '焊接设备' OR industry = '切割设备'
       OR industry = '铸造' OR industry = '锻造' OR industry = '钣金加工'
       OR industry = '模具' OR industry = '自动化设备' OR industry = '包装机械'
       OR industry = '食品机械' OR industry = '纺织机械' OR industry = '印刷机械'
       OR industry = '化工设备' OR industry = '环保设备' OR industry = '锅炉'
       OR industry = '阀门' OR industry = '泵' OR industry = '压缩机'
       OR industry = '风机' OR industry = '电机电气' OR industry = '仪器仪表'
       OR industry = '五金工具' OR industry = '标准件' OR industry = '润滑油'
       OR industry = '汽摩配件' OR industry = '金属加工' OR industry = '通用机械'
    GROUP BY industry
    ORDER BY count DESC
''')
stats = c.fetchall()

print(f'{"Sub-industry":<20} {"Count":<10} {"With Phone":<12} {"Rate":<10}')
print('-'*60)
total = 0
with_phone = 0
for s in stats:
    rate = s['has_phone'] / s['count'] * 100 if s['count'] > 0 else 0
    print(f'{s["industry"]:<20} {s["count"]:<10} {s["has_phone"]:<12} {rate:>6.1f}%')
    total += s['count']
    with_phone += s['has_phone']

print('-'*60)
print(f'{"TOTAL":<20} {total:<10} {with_phone:<12} {with_phone/total*100:>6.1f}%')

# Show samples
print('\n' + '='*70)
print('[Sample Enterprises by Sub-industry]')
print('='*70)

for sub_ind in ['工程机械', '数控机床', '液压设备', '自动化设备', '模具', '轴承']:
    c.execute('''
        SELECT name, phone, district
        FROM customers
        WHERE industry = ? AND phone IS NOT NULL AND phone != ''
        LIMIT 3
    ''', (sub_ind,))
    samples = c.fetchall()
    if samples:
        print(f'\n{sub_ind}:')
        for s in samples:
            print(f'  - {s["name"][:30]}... | {s["phone"][:15]}... | {s["district"] or "N/A"}')

conn.close()

print('\n' + '='*70)
print('[Classification Complete]')
print('='*70)
