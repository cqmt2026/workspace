# -*- coding: utf-8 -*-
"""渠道效果对比表生成脚本"""
import sys, os, sqlite3, csv
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent')
sys.stdout.reconfigure(encoding='utf-8')

from scripts.modules.roi_calculator import generate_channel_comparison

print('='*60)
print('【渠道效果对比表】')
print('='*60)

# 连接数据库
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 获取客户数据
cur.execute('SELECT id, name, source, industry FROM customers LIMIT 500')
customers = [{'id': r[0], 'name': r[1], 'source': r[2], 'industry': r[3]} for r in cur.fetchall()]

# 获取通话记录
cur.execute('SELECT id, customer_id, result FROM call_logs LIMIT 100')
calls = [{'id': r[0], 'customer_id': r[1], 'result': r[2]} for r in cur.fetchall()]

conn.close()

# 生成对比表
comparison = generate_channel_comparison(customers, calls)

# 打印表格
print(f'\n{"渠道":<15} {"客户数":>8} {"潜在预算":>12} {"建议策略":>12}')
print('-'*60)
for channel, data in comparison.items():
    print(f'{channel:<15} {data["customer_count"]:>8} {data["total_potential_budget"]:>12,}元 {data["recommendation"]:>12}')
print('-'*60)
total_customers = sum(d['customer_count'] for d in comparison.values())
total_budget = sum(d['total_potential_budget'] for d in comparison.values())
print(f'{"总计":<15} {total_customers:>8} {total_budget:>12,}元')

print('\n' + '='*60)
print('【说明】')
print('1. 潜在预算 = 客户数 × 平均预算(3000元)')
print('2. 建议策略基于客户数量分级')
print('3. 详细转化率需积累通话数据后更新')
print('='*60)

# 导出CSV
output_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\channel_comparison.csv'
with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['渠道', '客户数', '潜在预算', '建议策略'])
    writer.writeheader()
    for channel, data in comparison.items():
        writer.writerow({
            '渠道': channel,
            '客户数': data['customer_count'],
            '潜在预算': data['total_potential_budget'],
            '建议策略': data['recommendation']
        })
print(f'\n✅ 对比表已导出: {output_path}')
