# -*- coding: utf-8 -*-
"""导入房产物业数据到CRM"""
import sys, csv, sqlite3, time, os
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/baidu_crm.db'
MASTER_DIR = 'data/master'

# 找最新的房产中介文件
files = [f for f in os.listdir(MASTER_DIR) if '房产中介' in f and f.endswith('.csv')]
if not files:
    print('ERROR: 未找到房产中介CSV文件')
    sys.exit(1)
realty_file = os.path.join(MASTER_DIR, sorted(files)[-1])
print(f'房产中介文件: {realty_file}')

files2 = [f for f in os.listdir(MASTER_DIR) if '物业服务' in f and f.endswith('.csv')]
if not files2:
    print('ERROR: 未找到物业服务CSV文件')
    sys.exit(1)
property_file = os.path.join(MASTER_DIR, sorted(files2)[-1])
print(f'物业服务文件: {property_file}')

def import_csv(csv_path, source_tag, industry_name):
    rows = csv.DictReader(open(csv_path, encoding='utf-8-sig'))
    items = list(rows)
    print(f'\n📂 {industry_name}: 读取 {len(items)} 条')
    
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
                name, industry_name, row.get('电话', ''), row.get('地址', ''),
                row.get('区域', ''), row.get('纬度', ''), row.get('经度', ''),
                source_tag, '待联系'
            ))
            ins += c.rowcount
        except Exception as e:
            print(f'  错误 {name}: {e}')
            skip += 1
    
    conn.commit()
    conn.close()
    has_phone = sum(1 for r in items if r.get('电话'))
    print(f'  有电话: {has_phone}家 ({round(has_phone/len(items)*100,1) if items else 0}%)')
    print(f'  ✅ 导入CRM: +{ins}条, 跳过{skip}条')
    return ins, skip

total_ins, total_skip = 0, 0

# 导入房产中介
ins1, skip1 = import_csv(realty_file, '高德POI-房产中介', '房产中介')
total_ins += ins1; total_skip += skip1

# 导入物业服务
ins2, skip2 = import_csv(property_file, '高德POI-物业服务', '物业服务')
total_ins += ins2; total_skip += skip2

# 验证
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM customers')
total = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
has_phone = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM customers WHERE industry = ?', ('房产中介',))
realty_count = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM customers WHERE industry = ?', ('物业服务',))
property_count = c.fetchone()[0]
conn.close()

print(f'\n{"=" * 50}')
print(f'【补抓完成】')
print(f'本次入库: +{total_ins}条')
print(f'房产中介CRM: {realty_count}家')
print(f'物业服务CRM: {property_count}家')
print(f'CRM总客户: {total:,}')
print(f'有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)')
