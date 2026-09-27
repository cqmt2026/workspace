import sqlite3, csv, os, sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
OUT_CSV = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\创新型中小企业_待补电话_1351家.csv'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
    SELECT id, name, district, address, source, tier
    FROM customers
    WHERE industry='创新型中小企业' AND (phone IS NULL OR phone='')
    ORDER BY id
""")
rows = c.fetchall()

# 按区域统计
print(f"待补电话总数: {len(rows)}家\n", flush=True)

district_count = {}
for r in rows:
    d = r[2] or '未知'
    district_count[d] = district_count.get(d, 0) + 1

print("按区域分布:")
for d, cnt in sorted(district_count.items(), key=lambda x: -x[1]):
    print(f"  {d}: {cnt}家")
print()

# 写入CSV
with open(OUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['id', '企业名称', '区域', '地址', '数据来源', '层级'])
    for r in rows:
        writer.writerow([r[0], r[1], r[2] or '', r[3] or '', r[4] or '', r[5] or ''])

print(f"已导出: {OUT_CSV}")
print(f"文件大小: {os.path.getsize(OUT_CSV)} 字节")

conn.close()
