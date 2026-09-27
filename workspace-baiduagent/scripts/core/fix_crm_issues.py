import sqlite3, re

conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c = conn.cursor()

# ═══════════════════════════════════════════
# FIX 1: 统一行业名称映射
# ═══════════════════════════════════════════
print("=== FIX 1: 统一行业名称 ===")

# 映射表
industry_map = {
    'Mechanical Equipment': '机械装备汽配',
    'New Materials': '新材料化工',
    '通用机械': '机械装备汽配',  # 合并到主类别
    '机械设备补充': '机械装备汽配',
    '新能源充电': '新能源充电电力',
    '教育培训': '教培机构',
    '教育培训补充': '教培机构',
    '能源环保补充': '环保检测',  # 合并到环保检测大类
}

for old, new in industry_map.items():
    c.execute(f"UPDATE customers SET industry = ? WHERE industry = ?", (new, old))
    count = c.rowcount
    print(f"  '{old}' -> '{new}': {count}条")

conn.commit()

# 验证
c.execute("SELECT DISTINCT industry FROM customers ORDER BY industry")
print("\n当前行业列表:")
for r in c.fetchall():
    print(f"  '{r[0]}'")

# ═══════════════════════════════════════════
# FIX 2: 清理 Mechanical Equipment 误分类
# ═══════════════════════════════════════════
print("\n=== FIX 2: 检查 Mechanical Equipment 残留 ===")
c.execute("SELECT COUNT(*) FROM customers WHERE industry = 'Mechanical Equipment'")
remaining = c.fetchone()[0]
print(f"  Mechanical Equipment残留: {remaining}条")

# 看看pending状态的name样本
c.execute("SELECT name, phone FROM customers WHERE industry = 'Mechanical Equipment' AND status = 'pending' LIMIT 10")
print("  样本:")
for r in c.fetchall():
    print(f"    {r[0]} | phone={r[1]}")

# ═══════════════════════════════════════════
# FIX 3: 坐标反推区域（483条有坐标无区域）
# ═══════════════════════════════════════════
print("\n=== FIX 3: 坐标反推区域 ===")
c.execute("""
    UPDATE customers 
    SET district = CASE
        WHEN address LIKE '%渝中区%' THEN '渝中区'
        WHEN address LIKE '%江北区%' OR address LIKE '%江北%' THEN '江北区'
        WHEN address LIKE '%渝北区%' OR address LIKE '%渝北%' THEN '渝北区'
        WHEN address LIKE '%南岸区%' OR address LIKE '%南岸%' THEN '南岸区'
        WHEN address LIKE '%九龙坡区%' OR address LIKE '%九龙坡%' THEN '九龙坡区'
        WHEN address LIKE '%沙坪坝区%' OR address LIKE '%沙坪坝%' THEN '沙坪坝区'
        WHEN address LIKE '%北碚区%' OR address LIKE '%北碚%' THEN '北碚区'
        WHEN address LIKE '%大渡口区%' OR address LIKE '%大渡口%' THEN '大渡口区'
        WHEN address LIKE '%巴南区%' OR address LIKE '%巴南%' THEN '巴南区'
        WHEN address LIKE '%高新区%' OR address LIKE '%高新%' THEN '重庆高新区'
        ELSE district
    END
    WHERE (district IS NULL OR district = '')
    AND lat IS NOT NULL AND lat != ''
    AND lng IS NOT NULL AND lng != ''
""")
geo_fixed = c.rowcount
print(f"  通过地址关键词补区域: {geo_fixed}条")

# ═══════════════════════════════════════════
# FIX 4: 仅地址关键词匹配（无坐标的）
# ═══════════════════════════════════════════
print("\n=== FIX 4: 地址关键词匹配区域 ===")
c.execute("""
    UPDATE customers 
    SET district = CASE
        WHEN address LIKE '%渝中区%' THEN '渝中区'
        WHEN address LIKE '%江北区%' OR address LIKE '%江北%' THEN '江北区'
        WHEN address LIKE '%渝北区%' OR address LIKE '%渝北%' THEN '渝北区'
        WHEN address LIKE '%南岸区%' OR address LIKE '%南岸%' THEN '南岸区'
        WHEN address LIKE '%九龙坡区%' OR address LIKE '%九龙坡%' THEN '九龙坡区'
        WHEN address LIKE '%沙坪坝区%' OR address LIKE '%沙坪坝%' THEN '沙坪坝区'
        WHEN address LIKE '%北碚区%' OR address LIKE '%北碚%' THEN '北碚区'
        WHEN address LIKE '%大渡口区%' OR address LIKE '%大渡口%' THEN '大渡口区'
        WHEN address LIKE '%巴南区%' OR address LIKE '%巴南%' THEN '巴南区'
        WHEN address LIKE '%高新区%' OR address LIKE '%高新%' THEN '重庆高新区'
        ELSE district
    END
    WHERE (district IS NULL OR district = '')
    AND address IS NOT NULL AND address != ''
""")
addr_fixed = c.rowcount
print(f"  通过地址关键词补区域: {addr_fixed}条")

conn.commit()

# ═══════════════════════════════════════════
# FIX 5: 自动分配缺失的Tier
# ═══════════════════════════════════════════
print("\n=== FIX 5: 自动分配缺失Tier ===")
# 有电话+核心行业 -> A类; 有电话其他 -> B类; 无电话 -> B类
c.execute("""
    UPDATE customers
    SET tier = CASE
        WHEN tier IS NULL OR tier = '' THEN
            CASE
                WHEN phone IS NOT NULL AND phone != '' AND industry IN ('口腔诊所','医美机构','教培机构','宠物医院','房产中介','装修装饰','母婴亲子') THEN 'A'
                WHEN phone IS NOT NULL AND phone != '' THEN 'B'
                ELSE 'B'
            END
        ELSE tier
    END
    WHERE tier IS NULL OR tier = ''
""")
tier_fixed = c.rowcount
print(f"  自动分配Tier: {tier_fixed}条")

conn.commit()

# ═══════════════════════════════════════════
# 最终验证
# ═══════════════════════════════════════════
print("\n=== 最终验证 ===")
c.execute("SELECT COUNT(*) FROM customers")
print(f"总客户: {c.fetchone()[0]}")

c.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
with_phone = c.fetchone()[0]
print(f"有电话: {with_phone} ({with_phone/14041*100:.1f}%)")

c.execute("SELECT COUNT(*) FROM customers WHERE district IS NOT NULL AND district != ''")
with_district = c.fetchone()[0]
print(f"有区域: {with_district} ({with_district/14041*100:.1f}%)")

c.execute("SELECT COUNT(*) FROM customers WHERE tier IS NOT NULL AND tier != ''")
with_tier = c.fetchone()[0]
print(f"有Tier: {with_tier} ({with_tier/14041*100:.1f}%)")

c.execute("SELECT DISTINCT industry FROM customers ORDER BY industry")
print(f"\n行业数: {len(c.fetchall())}")

# 检查是否还有Pending状态的机械类
c.execute("SELECT COUNT(*) FROM customers WHERE industry = 'Mechanical Equipment'")
mech_remaining = c.fetchone()[0]
print(f"Mechanical Equipment残留: {mech_remaining}")

# 检查pending状态总数
c.execute("SELECT COUNT(*) FROM customers WHERE status = 'pending'")
pending = c.fetchone()[0]
print(f"Pending状态总数: {pending}")

conn.close()
print("\n✅ 修复完成!")
