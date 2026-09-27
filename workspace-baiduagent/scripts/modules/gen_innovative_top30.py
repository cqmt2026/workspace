import sqlite3, json
from datetime import datetime

db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
c = conn.cursor()

# 获取创新型中小企业Top30(A类+有电话+有区域)
c.execute("""
SELECT name, phone, district, tier, source
FROM customers 
WHERE industry LIKE '%创新型%' 
AND tier='A' 
AND phone IS NOT NULL 
AND phone != '' 
AND phone != '无'
AND district IS NOT NULL 
AND district != ''
ORDER BY name
LIMIT 30
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
    print(f"{i:2d}. {name} | {phone} | {district}")

# 保存
out_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\assets\创新型中小企业Top30可拨打名单.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n已保存: {out_path}")

# 统计
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%' AND tier='A' AND phone IS NOT NULL AND phone != '' AND phone != '无' AND district IS NOT NULL AND district != ''")
total_target = c.fetchone()[0]
print(f"\n创新型中小企业核心目标(A类+有电话+有区域): {total_target}家")

conn.close()