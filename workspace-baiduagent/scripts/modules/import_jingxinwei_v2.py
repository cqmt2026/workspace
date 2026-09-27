# -*- coding: utf-8 -*-
"""批量导入经信委创新型中小企业到CRM"""
import openpyxl, sys, sqlite3, os, time
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\jingxinwei'
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
        district = str(row[2]).strip() if len(row) > 2 and row[2] else ''
        all_companies.append({'name': name, 'district': district})

print(f"准备导入: {len(all_companies)}家企业")

# 连接到CRM
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

inserted = 0
duplicated = 0
errors = 0

for i, c in enumerate(all_companies):
    try:
        # 检查是否已存在
        cur.execute("SELECT id FROM customers WHERE name=?", (c['name'],))
        if cur.fetchone():
            duplicated += 1
            continue
        
        # 插入新记录
        cur.execute(
            """INSERT INTO customers 
               (name, phone, industry, source, status, district)
               VALUES (?, '', ?, ?, ?, ?)""",
            (c['name'], '创新型中小企业', '经信委创新型中小企业2025', '待联系', c['district'])
        )
        inserted += 1
        if inserted % 100 == 0:
            print(f"  已导入 {inserted}/{len(all_companies)}...")
        time.sleep(0.005)
    except Exception as e:
        errors += 1

conn.commit()

# 验证
cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
has_phone = cur.fetchone()[0]

print(f"\n导入结果:")
print(f"  ✅ 新增入库: {inserted}家")
print(f"  ⏭️ 重复跳过: {duplicated}家")
print(f"  ❌ 错误: {errors}家")
print(f"  📊 CRM总客户: {total:,}家")
print(f"  📊 有电话: {has_phone:,}家 ({has_phone*100//total}%)")

conn.close()
