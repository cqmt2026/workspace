"""查询医疗类客户数量及状态分布"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM customers')
total = c.fetchone()[0]

med_keywords = ['医疗', '口腔', '医院', '医美', '妇科', '男科', '皮肤', '眼科', '肛肠', '精神', '综合医院', '妇科医院', '男科医院', '皮肤病医院']
pattern = ' OR '.join([f"industry LIKE '%{kw}%'" for kw in med_keywords])
c.execute(f'SELECT COUNT(*) FROM customers WHERE {pattern}')
med_total = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
med_phone = c.execute(f'SELECT COUNT(*) FROM customers WHERE {pattern} AND phone IS NOT NULL AND phone != ""').fetchone()[0]

print(f'总客户数: {total}')
print(f'医疗类客户数: {med_total}')
print(f'其中已有电话: {med_phone}')
print(f'需补电话: {med_total - med_phone}')

# 行业细分
for kw in med_keywords:
    cnt = c.execute(f'SELECT COUNT(*) FROM customers WHERE industry LIKE "%{kw}%"').fetchone()[0]
    if cnt > 0:
        print(f'  - {kw}: {cnt}家')

conn.close()
