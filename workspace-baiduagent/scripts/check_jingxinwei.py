# -*- coding: utf-8 -*-
"""检查经信委数据与CRM的匹配情况"""
import sqlite3, sys, csv, os
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
MASTER_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'

print("=" * 70)
print("【经信委数据质量分析】")
print("=" * 70)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. 检查经信委来源的企业数量
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%创新型%' OR source LIKE '%经信委%'")
jc_count = cur.fetchone()[0]
print(f"\n📊 经信委来源企业: {jc_count}家")

# 2. 检查这些企业的电话覆盖率
if jc_count > 0:
    cur.execute("""
        SELECT COUNT(*) FROM customers 
        WHERE (source LIKE '%创新型%' OR source LIKE '%经信委%') 
        AND phone IS NOT NULL AND phone != ''
    """)
    has_tel = cur.fetchone()[0]
    print(f"   有电话: {has_tel}家 ({has_tel*100//jc_count}%)")

# 3. 检查经信委Excel中的前5条与CRM匹配情况
print("\n🔍 经信委数据与CRM匹配检查:")
excel_names = []
with open(os.path.join(MASTER_DIR, '创新型中小企业_jingxinwei_2025.csv'), encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        excel_names.append(row['name'])
        if len(excel_names) >= 5:
            break

for name in excel_names:
    cur.execute("SELECT id, name, industry, source, phone FROM customers WHERE name=?", (name,))
    result = cur.fetchone()
    if result:
        print(f"  ✅ 匹配: {name[:30]}... | 行业={result[2]} | 来源={result[3]} | 电话={'有' if result[4] else '无'}")
    else:
        print(f"  ❌ 未匹配: {name[:30]}...")

# 4. 分析低覆盖率行业的数据来源
print("\n📊 低覆盖率行业数据来源分析:")
cur.execute("""
    SELECT c.industry, COUNT(*) as total,
           SUM(CASE WHEN c.phone IS NOT NULL AND c.phone != '' THEN 1 ELSE 0 END) as has_phone,
           SUM(CASE WHEN c.source LIKE '%高德%' OR c.source LIKE '%百度%' OR c.source LIKE '%腾讯%' THEN 1 ELSE 0 END) as map_source,
           SUM(CASE WHEN c.source LIKE '%专精特新%' OR c.source LIKE '%创新型%' OR c.source LIKE '%经信委%' THEN 1 ELSE 0 END) as official_source
    FROM customers c
    WHERE c.industry IN ('软件信息','智能制造','物流货运','检验检测','电子科技','食品加工','能源环保补充','人力资源','教育培训补充')
    GROUP BY c.industry
    ORDER BY total DESC
""")
print(f"   {'行业':<12} {'总数':>6} {'有电话':>8} {'覆盖率':>8} {'地图':>6} {'官方':>6}")
print("   " + "-" * 58)
for r in cur.fetchall():
    rate = r[2]*100//r[1] if r[1] else 0
    print(f"   {r[0]:<12} {r[1]:>6} {r[2]:>8} {rate:>5}% {r[3]:>6} {r[4]:>6}")

conn.close()
print("\n" + "=" * 70)
