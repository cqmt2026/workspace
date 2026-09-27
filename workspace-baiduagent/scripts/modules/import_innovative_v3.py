import csv, sqlite3, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
csv_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master\创新型中小企业_待补充名单.csv'

conn = sqlite3.connect(db)
c = conn.cursor()

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    rows = list(reader)

print(f"总行数: {len(rows)}")
valid_rows = rows[2:]  # 跳过两行表头
print(f"有效数据: {len(valid_rows)}家")

inserted = 0
skipped = 0
errors = 0

for row in valid_rows:
    if len(row) < 2:
        continue
    seq = row[0].strip()
    name = row[1].strip()
    district = row[2].strip() if len(row) > 2 else ''
    
    if not name or name == '企业名称':
        continue
    
    try:
        c.execute("SELECT id FROM customers WHERE name = ?", (name,))
        if c.fetchone():
            skipped += 1
            continue
        
        c.execute("""
            INSERT INTO customers (name, industry, district, tier, source, status, created_at, updated_at)
            VALUES (?, '创新型中小企业', ?, 'A', '经信委创新型中小企业-补充名单', '待联系', ?, ?)
        """, (name, district, datetime.now().strftime('%Y-%m-%d %H:%M'), datetime.now().strftime('%Y-%m-%d %H:%M')))
        inserted += c.rowcount
        
    except Exception as e:
        errors += 1
        if errors <= 3:
            print(f"  错误: {name} - {e}")

conn.commit()
conn.close()

print(f"\n导入完成:")
print(f"  新增: {inserted}家")
print(f"  跳过(已存在): {skipped}家")
print(f"  错误: {errors}家")