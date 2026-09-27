# -*- coding: utf-8 -*-
"""抓取总结与建议"""
import sys, os, sqlite3, csv, glob
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

# CRM统计
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()
cur.execute("SELECT industry, COUNT(*) FROM customers GROUP BY industry ORDER BY COUNT(*) DESC")
total_customers = 0
total_with_phone = 0
cur.execute("SELECT industry, COUNT(*), SUM(CASE WHEN phone != '' THEN 1 ELSE 0 END) FROM customers GROUP BY industry ORDER BY COUNT(*) DESC")
row_data = []
for ind, cnt, ph in cur.fetchall():
    row_data.append((ind, cnt, ph))
    total_customers += cnt
    total_with_phone += ph
conn.close()

print("=" * 60)
print("📊 百度地图数据抓取总结")
print("=" * 60)
print(f"\nCRM总计: {total_customers} 家客户, 有电话 {total_with_phone} 家 ({total_with_phone/total_customers*100:.0f}%)")
print(f"\n行业分布:")
for ind, cnt, ph in row_data:
    pct = ph/cnt*100 if cnt > 0 else 0
    print(f"  {ind}: {cnt:4d}家, 电话{ph:4d}家 ({pct:3.0f}%)")

# master文件统计
print(f"\n{'='*60}")
print("📁 master CSV文件统计")
print("=" * 60)
total_rows = 0
for f in sorted(glob.glob('data/master/*_baidu.csv')):
    fname = os.path.basename(f)
    with open(f, encoding='utf-8-sig', errors='ignore') as fh:
        lines = fh.readlines()
    print(f"  {fname}: {len(lines)}条")
    total_rows += len(lines)
print(f"  合计: {total_rows}条")
