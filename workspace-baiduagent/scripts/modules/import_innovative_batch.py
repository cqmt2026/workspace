import csv, sqlite3
from datetime import datetime

db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
csv_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master\创新型中小企业_待补充名单.csv'

conn = sqlite3.connect(db)
c = conn.cursor()

# 读取CSV,提取企业名称和区县
companies = []
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    headers = next(reader)  # 第一行表头
    headers2 = next(reader)  # 第二行表头
    for row in reader:
        if len(row) >= 2:
            name = row[1].strip()
            district = row[2].strip() if len(row) > 2 else ''
            if name and name != '企业名称':
                companies.append({'name': name, 'district': district})

print(f"从CSV读取: {len(companies)}家企业")

# 检查哪些已入库
existing = 0
new_companies = []
for comp in companies:
    c.execute("SELECT id FROM customers WHERE name = ?", (comp['name'],))
    if c.fetchone():
        existing += 1
    else:
        new_companies.append(comp)

print(f"已入库: {existing}家")
print(f"需新增: {len(new_companies)}家")

# 批量插入
inserted = 0
batch = []
for comp in new_companies[:100]:  # 先测试前100家
    batch.append((comp['name'], '创新型中小企业', comp['district'], 'A', '经信委创新型中小企业-补充名单', '待联系'))
    inserted += 1

if batch:
    c.executemany("""
        INSERT INTO customers (name, industry, district, tier, source, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [(n, ind, dist, tier, src, stat, datetime.now(), datetime.now()) for n, ind, dist, tier, src, stat in batch])
    conn.commit()

print(f"测试插入: {inserted}家")

# 统计最终状态
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%'")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%' AND phone IS NOT NULL AND phone != ''")
has_phone = c.fetchone()[0]

print(f"\n最终状态:")
print(f"  总数: {total}家")
print(f"  有电话: {has_phone}家 ({has_phone*100//total if total>0 else 0}%)")
print(f"  缺口: {total-has_phone}家")

conn.close()