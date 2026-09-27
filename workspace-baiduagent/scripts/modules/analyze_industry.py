"""分析数据库中的医院/体检行业分类"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3

conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
c = conn.cursor()

print('=== 数据库中的行业分类（包含"医院"、"体检"、"民营"） ===')

# 查询包含这些关键词的行业
c.execute("""
    SELECT DISTINCT industry, COUNT(*) as count 
    FROM customers 
    WHERE industry LIKE '%医院%' OR industry LIKE '%体检%' OR industry LIKE '%民营%'
    GROUP BY industry 
    ORDER BY count DESC
""")
rows = c.fetchall()
for row in rows:
    print(f'{row[0]}: {row[1]}家')

print('\n=== 随机抽取20条医院类客户 ===')
c.execute("""
    SELECT name, industry, phone, district 
    FROM customers 
    WHERE industry LIKE '%医院%' 
    LIMIT 20
""")
rows = c.fetchall()
for row in rows:
    print(f'{row[0]} | {row[1]} | {row[2]} | {row[3]}')

conn.close()
