# -*- coding: utf-8 -*-
"""导入物业服务数据到CRM"""
import sys, os, csv, sqlite3, time
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/baidu_crm.db'
MASTER_DIR = 'data/master'

files = [f for f in os.listdir(MASTER_DIR) if '物业服务' in f and f.endswith('.csv')]
if not files:
    print('ERROR: 未找到物业服务CSV')
    sys.exit(1)
property_file = os.path.join(MASTER_DIR, sorted(files)[-1])
print(f'物业服务文件: {property_file}')

rows = csv.DictReader(open(property_file, encoding='utf-8-sig'))
items = list(rows)
print(f'读取 {len(items)} 条')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
ins = skip = 0
for row in items:
    name = row.get('机构名称', '').strip()
    if not name:
        continue
    c.execute('SELECT id FROM customers WHERE name = ?', (name,))
    if c.fetchone():
        skip += 1
        continue
    try:
        c.execute('''
            INSERT INTO customers(name, industry, phone, address, district, lat, lng, source, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        ''', (
            name, '物业服务', row.get('电话', ''), row.get('地址', ''),
            row.get('区域', ''), row.get('纬度', ''), row.get('经度', ''),
            '高德POI-物业服务', '待联系'
        ))
        ins += c.rowcount
    except Exception as e:
        print(f'  导入错误 {name}: {e}')
        skip += 1

conn.commit()
conn.close()
has_phone = sum(1 for r in items if r.get('电话'))
print(f'✅ 导入CRM: +{ins}条, 跳过{skip}条')
print(f'   有电话: {has_phone}家 ({round(has_phone/len(items)*100,1) if items else 0}%)')

# 验证
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM customers')
total = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM customers WHERE industry = ?', ('物业服务',))
property_count = c.fetchone()[0]
conn.close()
print(f'CRM总客户: {total:,}')
print(f'物业服务行业: {property_count}家')
