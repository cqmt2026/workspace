# -*- coding: utf-8 -*-
"""CRM客户详情展示"""
import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()

# 总数
c.execute('SELECT COUNT(*) FROM customers')
total = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
has_phone = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM customers WHERE tier IS NOT NULL')
has_tier = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM customers WHERE district IS NOT NULL AND district != ""')
has_district = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM customers WHERE status = "待联系"')
pending = c.fetchone()[0]

print('=' * 70)
print(f'【CRM总览】总客户: {total:,}家 | 有电话: {has_phone:,} ({round(has_phone/total*100,1)}%) | 有层级: {has_tier:,} | 有区域: {has_district:,} | 待联系: {pending:,}')
print('=' * 70)

# 行业分布
print('\n【行业分布 Top30】')
print(f'{"行业":<20} {"总数":>8} {"有电话":>8} {"覆盖率":>8} {"层级A":>6} {"层级B":>6}')
print('-' * 65)
c.execute('''
    SELECT industry, COUNT(*) as cnt,
           SUM(CASE WHEN phone IS NOT NULL AND phone != "" THEN 1 ELSE 0 END) as phones,
           SUM(CASE WHEN tier = "A" THEN 1 ELSE 0 END) as tier_a,
           SUM(CASE WHEN tier = "B" THEN 1 ELSE 0 END) as tier_b
    FROM customers GROUP BY industry ORDER BY cnt DESC LIMIT 30
''')
for r in c.fetchall():
    cov = round(r[2]/r[1]*100,1) if r[1] else 0
    print(f'{r[0]:<20} {r[1]:>8} {r[2]:>8} {cov:>7.1f}% {r[3]:>6} {r[4]:>6}')

# 区域分布
print('\n【区域分布】')
print(f'{"区域":<12} {"数量":>8}')
print('-' * 22)
c.execute('SELECT district, COUNT(*) as cnt FROM customers WHERE district IS NOT NULL AND district != "" GROUP BY district ORDER BY cnt DESC')
for r in c.fetchall():
    print(f'{r[0]:<12} {r[1]:>8}')

# 最近入库
print('\n【最近20条入库记录】')
print(f'{"ID":>5} {"企业名称":<30} {"行业":<12} {"电话":<15} {"区域":<8} {"来源"}')
print('-' * 90)
c.execute('SELECT id, name, industry, phone, district, source FROM customers ORDER BY id DESC LIMIT 20')
for r in c.fetchall():
    name = r[1][:28] if r[1] else ''
    phone = r[3] if r[3] else '无'
    print(f'{r[0]:>5} {name:<30} {r[2]:<12} {phone:<15} {r[4] or "-":<8} {r[5]}')

conn.close()
