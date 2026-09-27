import csv, sqlite3
from datetime import datetime

db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
csv_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master\创新型中小企业_待补充名单.csv'

conn = sqlite3.connect(db)
c = conn.cursor()

# 读取CSV
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    rows = list(reader)

print(f"总行数: {len(rows)}")
print(f"表头: {rows[0]}")

# 跳过表头,从第2行开始
valid_rows = rows[1:]
print(f"数据行: {len(valid_rows)}家")

# 导入CRM
inserted = 0
skipped = 0
errors = 0

for row in valid_rows:
    if len(row) < 2:
        continue
    
    # 格式: 序号,企业名称,区县
    seq = row[0].strip()
    name = row[1].strip()
    district = row[2].strip() if len(row) > 2 else ''
    
    if not name or name == '企业名称':
        continue
    
    try:
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
        
    except Exception as e:
        errors += 1
        if errors <= 5:
            print(f"  错误: {name} - {e}")

conn.commit()
conn.close()

print(f"\n✅ 导入完成:")
print(f"  新增: {inserted}家")
print(f"  跳过(已存在): {skipped}家")
print(f"  错误: {errors}家")