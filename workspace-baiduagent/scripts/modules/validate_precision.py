import sqlite3, json
db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
c = conn.cursor()

print("=" * 60)
print("【精准客户筛选 - 数据验证版】")
print("=" * 60)

# ========== 维度1: 需求强度 ==========
print("\n【维度1: 需求强度 - 搜索行为代理指标】")
print("→ 用'百度竞争程度'作为代理指标(同行业在百度投放越少=蓝海越大)")

# 各行业百度竞争程度(估算: 基于电话覆盖率+来源质量)
c.execute("""
SELECT industry, COUNT(*) as total, 
       SUM(CASE WHEN phone != '无' AND phone != '' THEN 1 ELSE 0 END) as with_phone,
       SUM(CASE WHEN source LIKE '%经信委%' OR source LIKE '%卫健委%' OR source LIKE '%专精特新%' THEN 1 ELSE 0 END) as official_source
FROM customers
GROUP BY industry
ORDER BY total DESC
LIMIT 20
""")
rows = c.fetchall()
print("\n行业规模 vs 官方数据来源比例(代表企业正规度/需求强度):")
print(f"{'行业':<15} {'总数':>6} {'有电话':>8} {'官方来源':>10} {'电话率':>8} {'官方率':>8}")
for ind, total, phone, official in rows:
    phone_rate = phone*100//total if total > 0 else 0
    official_rate = official*100//total if total > 0 else 0
    print(f"{ind:<15} {total:>6} {phone:>8} {official:>10} {phone_rate:>7}% {official_rate:>7}%")

# ========== 维度2: 支付能力 ==========
print("\n\n【维度2: 支付能力 - Tier分层+规模代理】")
c.execute("SELECT tier, COUNT(*) FROM customers GROUP BY tier ORDER BY tier")
tier_stats = c.fetchall()
print(f"\n客户分层统计:")
for tier, cnt in tier_stats:
    print(f"  {tier}: {cnt}家 ({cnt*100//14041}%)")

# A类客户的电话覆盖率 vs B类
c.execute("""
SELECT tier, 
       COUNT(*) as total,
       SUM(CASE WHEN phone != '无' AND phone != '' THEN 1 ELSE 0 END) as with_phone
FROM customers
GROUP BY tier
""")
tier_phone = c.fetchall()
print(f"\n各层级电话覆盖率(代表线索质量):")
for tier, total, phone in tier_phone:
    rate = phone*100//total if total > 0 else 0
    print(f"  {tier}: {phone}/{total} ({rate}%)")

# ========== 维度3: 决策权 ==========
print("\n\n【维度3: 决策权 - 企业类型判断】")
# 有contact字段的客户(更可能是决策人或关键联系人)
c.execute("SELECT COUNT(*) FROM customers WHERE contact IS NOT NULL AND contact != '' AND contact != '无'")
with_contact = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE contact IS NULL OR contact = '' OR contact = '无'")
no_contact = c.fetchone()[0]
print(f"有联系人信息: {with_contact}家 ({with_contact*100//14041}%)")
print(f"无联系人信息: {no_contact}家 ({no_contact*100//14041}%)")

# ========== 维度4: 竞争强度 ==========
print("\n\n【维度4: 竞争强度 - 电话覆盖率反推】")
print("→ 逻辑: 电话覆盖率越低,说明该行业线上获客越少,蓝海程度越高")
c.execute("""
SELECT industry, COUNT(*) as total,
       SUM(CASE WHEN phone != '无' AND phone != '' THEN 1 ELSE 0 END) as with_phone
FROM customers
GROUP BY industry
ORDER BY total DESC
LIMIT 30
""")
rows = c.fetchall()
print(f"\n{'行业':<15} {'总数':>6} {'有电话':>8} {'覆盖率':>8} {'竞争度':>6}")
for ind, total, phone in rows:
    rate = phone*100//total if total > 0 else 0
    # 覆盖率<30% = 蓝海, 30-60% = 中等, >60% = 红海
    if rate < 30:
        competition = "蓝海"
    elif rate < 60:
        competition = "中等"
    else:
        competition = "红海"
    print(f"{ind:<15} {total:>6} {phone:>8} {rate:>7}% {competition:>6}")

# ========== 维度5: 触达成本 ==========
print("\n\n【维度5: 触达成本 - 区域分布+电话可达性】")
c.execute("""
SELECT district, COUNT(*) as total,
       SUM(CASE WHEN phone != '无' AND phone != '' THEN 1 ELSE 0 END) as with_phone
FROM customers
GROUP BY district
ORDER BY total DESC
LIMIT 15
""")
dist_rows = c.fetchall()
print(f"\n{'区域':<12} {'总数':>6} {'有电话':>8} {'覆盖率':>8} {'建议':>6}")
for dist, total, phone in dist_rows:
    rate = phone*100//total if total > 0 else 0
    suggestion = "重点" if rate > 50 else ("一般" if rate > 30 else "待补")
    print(f"{dist:<12} {total:>6} {phone:>8} {rate:>7}% {suggestion:>6}")

conn.close()