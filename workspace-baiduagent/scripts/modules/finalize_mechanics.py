import sqlite3, json
db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
c = conn.cursor()

# 机械行业完整统计
c.execute("""
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN phone != '' AND phone IS NOT NULL THEN 1 ELSE 0 END) as with_phone,
    SUM(CASE WHEN tier='A' THEN 1 ELSE 0 END) as tier_a,
    SUM(CASE WHEN tier='A' AND phone != '' AND phone IS NOT NULL THEN 1 ELSE 0 END) as tier_a_with_phone,
    SUM(CASE WHEN district IS NOT NULL AND district != '' THEN 1 ELSE 0 END) as with_district
FROM customers WHERE industry LIKE '%机械%'
""")
row = c.fetchone()
print("=" * 60)
print("【机械装备汽配行业 - 最终数据】")
print("=" * 60)
print(f"总客户数: {row[0]}家")
print(f"有电话: {row[1]}家 ({row[1]*100//row[0] if row[0]>0 else 0}%)")
print(f"A类客户: {row[2]}家")
print(f"A类+有电话: {row[3]}家 (核心拨打目标)")
print(f"有区域: {row[4]}家 ({row[4]*100//row[0] if row[0]>0 else 0}%)")

# 按区域分布
print("\n【按区域分布】")
c.execute("""
SELECT district, COUNT(*) as cnt,
       SUM(CASE WHEN phone != '' AND phone IS NOT NULL THEN 1 ELSE 0 END) as with_phone
FROM customers WHERE industry LIKE '%机械%' AND district IS NOT NULL AND district != ''
GROUP BY district ORDER BY cnt DESC
""")
for dist, cnt, phone in c.fetchall():
    print(f"  {dist}: {cnt}家 (有电话{phone}家)")

# 按来源分布
print("\n【按数据来源分布】")
c.execute("""
SELECT source, COUNT(*) FROM customers WHERE industry LIKE '%机械%'
GROUP BY source ORDER BY COUNT(*) DESC
""")
for src, cnt in c.fetchall():
    print(f"  {src}: {cnt}家")

# 生成Top30可拨打名单(A类+有电话+有区域)
print("\n【Top30可拨打名单(A类+有电话+有区域)】")
c.execute("""
SELECT name, phone, district, tier, source
FROM customers 
WHERE industry LIKE '%机械%' AND tier='A' AND phone != '' AND phone IS NOT NULL AND district IS NOT NULL AND district != ''
ORDER BY name
LIMIT 30
""")
results = []
for i, row in enumerate(c.fetchall(), 1):
    name, phone, district, tier, source = row
    results.append({"序号": i, "公司名": name, "电话": phone, "区域": district, "层级": tier, "来源": source})
    print(f"{i:2d}. {name} | {phone} | {district}")

# 保存
out_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets\机械行业Top30可拨打名单.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n✅ 已保存: {out_path}")

conn.close()