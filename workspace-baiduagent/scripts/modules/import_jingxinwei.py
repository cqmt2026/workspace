# -*- coding: utf-8 -*-
"""解析经信委数据并批量导入CRM"""
import openpyxl, sys, csv, sqlite3, os, time
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\jingxinwei'
MASTER_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

print("=" * 70)
print("【经信委创新型中小企业 - 批量导入CRM】")
print("=" * 70)

all_companies = []
for fname in ['2025_创新型_申报通过.xlsx', '2025_创新型_复核通过.xlsx']:
    fpath = os.path.join(BASE, fname)
    if not os.path.exists(fpath):
        continue
    wb = openpyxl.load_workbook(fpath, data_only=True)
    ws = wb.active
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        name = str(row[0]).strip() if row[0] else ''
        if not name or name == 'None':
            continue
        code = str(row[1]).strip() if len(row) > 1 and row[1] else ''
        district = str(row[2]).strip() if len(row) > 2 and row[2] else ''
        
        # 映射区县到主城区
        all_districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区','大渡口区','北碚区','巴南区','两江新区','重庆高新区']
        if district in all_districts or '科学城' in district:
            city = district.replace('西部科学城重庆高新区', '重庆高新区')
        else:
            city = '重庆'  # 其他区县
        
        all_companies.append({
            'name': name,
            'code': code,
            'district': district,
            'city': city,
            'industry': '创新型中小企业',
            'source': '经信委创新型中小企业2025'
        })

print(f"总企业数: {len(all_companies)}")

# 导入CRM
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

inserted = 0
duplicated = 0
for c in all_companies:
    try:
        cur.execute(
            "SELECT id FROM customers WHERE name=?", 
            (c['name'],)
        )
        if cur.fetchone():
            duplicated += 1
            continue
        
        cur.execute(
            """INSERT INTO customers (name, phone, address, industry, source, status, lat, lng, district)
               VALUES (?, '', '', ?, ?, ?, '', '', ?)""",
            (c['name'], c['industry'], c['source'], '待联系', c['district'])
        )
        inserted += 1
        time.sleep(0.01)
    except Exception as e:
        pass

conn.commit()
print(f"\n导入结果:")
print(f"  ✅ 新增入库: {inserted}家")
print(f"  ⏭️ 重复跳过: {duplicated}家")

# 验证
cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
print(f"  📊 CRM总客户: {total:,}家")
conn.close()
