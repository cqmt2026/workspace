# -*- coding: utf-8 -*-
"""多渠道客户统计脚本"""
import sys, os, sqlite3, csv
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent')
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 按source分组统计
cur.execute('''
    SELECT source, COUNT(*) as count 
    FROM customers 
    WHERE source IS NOT NULL AND source != ''
    GROUP BY source 
    ORDER BY count DESC
''')
rows = cur.fetchall()

print('='*70)
print('【全渠道客户统计】')
print('='*70)
print(f'{"渠道":<25} {"客户数":>10} {"占比":>8} {"潜在预算":>12} {"策略":>10}')
print('-'*70)

total = sum(r[1] for r in rows)
results = []
for src, count in rows:
    pct = count / total * 100 if total > 0 else 0
    budget = count * 3000
    if count >= 100:
        strategy = '重点投入'
    elif count >= 50:
        strategy = '持续关注'
    elif count >= 20:
        strategy = '适量投放'
    else:
        strategy = '测试阶段'
    print(f'{src:<25} {count:>10,} {pct:>7.1f}% {budget:>10,}元 {strategy:>10}')
    results.append({
        '渠道': src,
        '客户数': count,
        '占比': f'{pct:.1f}%',
        '潜在预算': budget,
        '建议策略': strategy
    })

print('-'*70)
print(f'{"总计":<25} {total:>10,} {"100.0":>7}% {total*3000:>10,}元')
print('='*70)

# 导出CSV
output_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\channel_statistics.csv'
with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['渠道', '客户数', '占比', '潜在预算', '建议策略'])
    writer.writeheader()
    writer.writerows(results)
print(f'\n✅ 统计结果已导出: {output_path}')

conn.close()
