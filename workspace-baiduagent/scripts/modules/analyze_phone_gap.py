import sqlite3, json
db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
c = conn.cursor()

print("=" * 70)
print("【电话补充需求分析】")
print("=" * 70)

# Top3行业电话缺口统计
industries = ['创新型中小企业', '机械装备汽配', '口腔诊所']
results = []

for ind in industries:
    c.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN phone != '无' AND phone != '' AND phone IS NOT NULL THEN 1 ELSE 0 END) as with_phone,
        SUM(CASE WHEN phone = '无' OR phone = '' OR phone IS NULL THEN 1 ELSE 0 END) as no_phone
    FROM customers WHERE industry LIKE '%{ind}%'
    """.format(ind=ind))
    row = c.fetchone()
    total, with_phone, no_phone = row
    gap = no_phone if no_phone else 0
    gap_rate = gap * 100 // total if total > 0 else 0
    print(f"\n【{ind}】")
    print(f"  总数: {total}家")
    print(f"  有电话: {with_phone}家 ({with_phone*100//total if total>0 else 0}%)")
    print(f"  缺电话: {gap}家 ({gap_rate}%)")
    results.append({"行业": ind, "总数": total, "有电话": with_phone, "缺电话": gap, "缺口率": f"{gap_rate}%"})

# 全库缺口统计
c.execute("""
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN phone != '无' AND phone != '' AND phone IS NOT NULL THEN 1 ELSE 0 END) as with_phone,
    SUM(CASE WHEN phone = '无' OR phone = '' OR phone IS NULL THEN 1 ELSE 0 END) as no_phone
FROM customers
""")
row = c.fetchone()
total, with_phone, no_phone = row
print(f"\n【全库汇总】")
print(f"  总数: {total}家")
print(f"  有电话: {with_phone}家 ({with_phone*100//total}%)")
print(f"  缺电话: {no_phone}家 ({no_phone*100//total}%)")

# 按行业看缺口最大的Top10
print("\n\n【各行业电话缺口Top10】")
c.execute("""
SELECT industry, 
       COUNT(*) as total,
       SUM(CASE WHEN phone != '无' AND phone != '' AND phone IS NOT NULL THEN 1 ELSE 0 END) as with_phone,
       COUNT(*) - SUM(CASE WHEN phone != '无' AND phone != '' AND phone IS NOT NULL THEN 1 ELSE 0 END) as gap
FROM customers
GROUP BY industry
ORDER BY gap DESC
LIMIT 10
""")
rows = c.fetchall()
print(f"{'行业':<15} {'总数':>6} {'有电话':>8} {'缺电话':>8} {'缺口率':>8}")
for ind, total, phone, gap in rows:
    rate = gap * 100 // total if total > 0 else 0
    print(f"{ind:<15} {total:>6} {phone:>8} {gap:>8} {rate:>7}%")

conn.close()