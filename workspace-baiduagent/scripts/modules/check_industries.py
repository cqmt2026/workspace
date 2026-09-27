import sqlite3
db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(db)
c = conn.cursor()

# 1. 总体统计
c.execute("SELECT COUNT(*) FROM customers")
total = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != '' AND phone != '无'")
with_phone = c.fetchone()[0]

print(f'=== 总客户数: {total} ===')
print(f'有电话: {with_phone} ({with_phone*100//total}%)')

# 2. Top30行业
c.execute("SELECT industry, COUNT(*) as cnt FROM customers GROUP BY industry ORDER BY cnt DESC LIMIT 30")
industries = c.fetchall()
print('\n=== Top30行业 ===')
for ind, cnt in industries[:30]:
    print(f'{ind}: {cnt}')

# 3. 空调/暖通相关
c.execute("SELECT industry, COUNT(*) FROM customers WHERE industry LIKE '%空调%' OR industry LIKE '%暖通%' OR industry LIKE '%中央%' OR industry LIKE '%制冷%' GROUP BY industry")
ac = c.fetchall()
print('\n=== 空调/暖通相关 ===')
for ind, cnt in ac:
    print(f'{ind}: {cnt}')

# 4. 机械相关
c.execute("SELECT industry, COUNT(*) FROM customers WHERE industry LIKE '%机械%' OR industry LIKE '%装备%' OR industry LIKE '%精密%' OR industry LIKE '%液压%' OR industry LIKE '%传动%' OR industry LIKE '%轴承%' OR industry LIKE '%锻造%' OR industry LIKE '%齿轮%' OR industry LIKE '%电机%' OR industry LIKE '%风机%' OR industry LIKE '%压缩机%' GROUP BY industry ORDER BY COUNT(*) DESC")
mfg = c.fetchall()
print('\n=== 机械/装备制造 ===')
for ind, cnt in mfg:
    print(f'{ind}: {cnt}')

# 5. 餐饮
c.execute("SELECT industry, COUNT(*) FROM customers WHERE industry LIKE '%餐饮%' OR industry LIKE '%火锅%' OR industry LIKE '%美食%' OR industry LIKE '%酒楼%' OR industry LIKE '%茶馆%' GROUP BY industry ORDER BY COUNT(*) DESC")
food = c.fetchall()
print('\n=== 餐饮相关 ===')
for ind, cnt in food:
    print(f'{ind}: {cnt}')

# 6. 装修
c.execute("SELECT industry, COUNT(*) FROM customers WHERE industry LIKE '%装修%' OR industry LIKE '%装饰%' OR industry LIKE '%建材%' GROUP BY industry ORDER BY COUNT(*) DESC")
reno = c.fetchall()
print('\n=== 装修装饰 ===')
for ind, cnt in reno:
    print(f'{ind}: {cnt}')

# 7. 医疗
c.execute("SELECT industry, COUNT(*) FROM customers WHERE industry LIKE '%医疗%' OR industry LIKE '%医院%' OR industry LIKE '%口腔%' OR industry LIKE '%医美%' OR industry LIKE '%体检%' GROUP BY industry ORDER BY COUNT(*) DESC")
med = c.fetchall()
print('\n=== 医疗相关 ===')
for ind, cnt in med:
    print(f'{ind}: {cnt}')

conn.close()