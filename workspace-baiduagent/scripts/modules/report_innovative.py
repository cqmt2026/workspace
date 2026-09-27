import sqlite3, json
from datetime import datetime

db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
c = conn.cursor()

print("=" * 70)
print("【创新型中小企业 - 最终数据报告】")
print("=" * 70)

# 总体统计
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%'")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%' AND phone IS NOT NULL AND phone != ''")
has_phone = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%' AND tier='A'")
tier_a = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%' AND tier='A' AND phone IS NOT NULL AND phone != ''")
tier_a_phone = c.fetchone()[0]

print(f"\n总体:")
print(f"  总数: {total}家")
print(f"  有电话: {has_phone}家 ({has_phone*100//total if total>0 else 0}%)")
print(f"  A类: {tier_a}家")
print(f"  A类+有电话: {tier_a_phone}家")

# 按区域分布
print(f"\n【按区域分布(Top10)】")
c.execute("""
SELECT district, COUNT(*) as cnt,
       SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as with_phone
FROM customers WHERE industry LIKE '%创新型%' AND district IS NOT NULL AND district != ''
GROUP BY district ORDER BY cnt DESC LIMIT 10
""")
for dist, cnt, phone in c.fetchall():
    print(f"  {dist}: {cnt}家 (有电话{phone}家)")

# Top50可拨打名单
print(f"\n【Top50可拨打名单(A类+有电话+有区域)】")
c.execute("""
SELECT name, phone, district, tier, source
FROM customers 
WHERE industry LIKE '%创新型%' 
AND tier='A' 
AND phone IS NOT NULL 
AND phone != '' 
AND district IS NOT NULL 
AND district != ''
ORDER BY name
LIMIT 50
""")

results = []
for i, row in enumerate(c.fetchall(), 1):
    name, phone, district, tier, source = row
    results.append({
        "序号": i,
        "公司名": name,
        "电话": phone,
        "区域": district,
        "层级": tier,
        "来源": source
    })
    print(f"{i:2d}. {name} | {phone[:20]}... | {district}")

# 保存
out_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets\创新型中小企业Top50可拨打名单_v2.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n已保存: {out_path}")

conn.close()