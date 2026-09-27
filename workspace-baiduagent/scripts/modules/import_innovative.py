import csv, sqlite3, os
from datetime import datetime

db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
csv_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master\创新型中小企业_待补充名单.csv'

conn = sqlite3.connect(db)
c = conn.cursor()

# 读取CSV
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = [row for row in reader]

print(f"待补充名单: {len(rows)}家")

# 过滤有效行(跳过表头)
valid_rows = [r for r in rows if r.get('name') and r['name'].strip().isdigit() == False]
print(f"有效数据: {len(valid_rows)}家")

# 导入CRM
inserted = 0
skipped = 0
for row in valid_rows:
    name = row.get('code', '').strip()
    district = row.get('district', '').strip()
    
    if not name:
        continue
    
    # 检查是否已存在
    c.execute("SELECT id FROM customers WHERE name = ?", (name,))
    if c.fetchone():
        skipped += 1
        continue
    
    # 插入
    c.execute("""
        INSERT INTO customers (name, industry, district, tier, source, status, created_at, updated_at)
        VALUES (?, '创新型中小企业', ?, 'A', '经信委创新型中小企业-补充名单', '待联系', ?, ?)
    """, (name, district, datetime.now().strftime('%Y-%m-%d %H:%M'), datetime.now().strftime('%Y-%m-%d %H:%M')))
    inserted += c.rowcount

conn.commit()
conn.close()

print(f"\n导入完成:")
print(f"  新增: {inserted}家")
print(f"  跳过(已存在): {skipped}家")
print(f"  总计待补充: {len(valid_rows)}家")