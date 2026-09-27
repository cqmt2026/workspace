import csv, sqlite3, os
from datetime import datetime

db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
c = conn.cursor()

# 统计当前状态
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%'")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%' AND phone IS NOT NULL AND phone != ''")
has_phone = c.fetchone()[0]

print(f"创新型中小企业:")
print(f"  总数: {total}家")
print(f"  有电话: {has_phone}家 ({has_phone*100//total if total>0 else 0}%)")
print(f"  缺口: {total-has_phone}家")

# 查看待补充名单文件
csv_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master\创新型中小企业_待补充名单.csv'
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    rows = list(reader)

print(f"\nCSV文件:")
print(f"  总行数: {len(rows)}")
print(f"  有效数据: {len(rows)-2}家(跳过2行表头)")

# 检查哪些已入库
existing = 0
new_count = 0
for row in rows[2:]:  # 跳过两行表头
    if len(row) < 2:
        continue
    name = row[1].strip()
    if not name:
        continue
    c.execute("SELECT id FROM customers WHERE name = ?", (name,))
    if c.fetchone():
        existing += 1
    else:
        new_count += 1

print(f"\nCSV与CRM对比:")
print(f"  已入库: {existing}家")
print(f"  未入库: {new_count}家")

conn.close()