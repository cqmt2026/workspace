import sqlite3, json
db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("""
SELECT name, industry, phone, district, tier, source 
FROM customers 
WHERE industry LIKE '%口腔%'
AND phone IS NOT NULL AND phone != '' AND phone != '无'
ORDER BY tier ASC, name
LIMIT 50
""")
rows = c.fetchall()
print(f"=== 口腔诊所有电话: {len(rows)}家 ===\n")
results = []
for row in rows[:30]:
    name, ind, phone, district, tier, source = row
    results.append({"序号": len(results)+1, "公司名": name, "行业": ind, "电话": phone, "区域": district, "层级": tier, "来源": source})
    print(f"{len(results):2d}. {name} | {phone} | {district} | {tier}")
with open(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets\口腔诊所精准名单_top30.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n✅ 已保存: assets/口腔诊所精准名单_top30.json")
conn.close()