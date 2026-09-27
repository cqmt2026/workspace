# -*- coding: utf-8 -*-
"""解析经信委Excel并比对CRM，输出待补充企业清单"""
import openpyxl, sys, sqlite3, csv, os
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\jingxinwei'
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
MASTER_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'

print("=" * 70)
print("【经信委创新型中小企业 - 解析与比对】")
print("=" * 70)

# 1. 读取Excel
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
        all_companies.append({'name': name, 'code': code, 'district': district})

print(f"Excel总企业: {len(all_companies)}家")

# 2. 比对CRM
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

existing = 0
new_companies = []
for c in all_companies:
    cur.execute("SELECT id FROM customers WHERE name=?", (c['name'],))
    if cur.fetchone():
        existing += 1
    else:
        new_companies.append(c)

print(f"CRM中已存在: {existing}家")
print(f"CRM中不存在: {len(new_companies)}家")

# 3. 保存待补充清单
out_path = os.path.join(MASTER_DIR, '创新型中小企业_待补充名单.csv')
with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['name','code','district'])
    writer.writeheader()
    for c in new_companies:
        writer.writerow(c)
print(f"待补充清单已保存: {out_path}")

# 4. 统计各区分布
districts = {}
for c in all_companies:
    d = c['district'] or '未知'
    districts[d] = districts.get(d, 0) + 1
print(f"\n📊 各区分布 (Top10):")
for d, cnt in sorted(districts.items(), key=lambda x: -x[1])[:10]:
    print(f"   {d}: {cnt}家")

conn.close()
