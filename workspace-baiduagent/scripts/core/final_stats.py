# -*- coding: utf-8 -*-
"""最终数据统计验证"""
import sys, os, csv, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

print("="*55)
print("📊 master数据源最终统计 (2026-08-29)")
print("="*55)
master_dir = 'data/master'
total = 0
for f in sorted(os.listdir(master_dir)):
    if f.endswith('.csv'):
        with open(os.path.join(master_dir, f), encoding='utf-8-sig') as fh:
            n = sum(1 for _ in fh) - 1
        total += n
        print(f"  {f}: {n}家")
print(f"  {'─'*40}")
print(f"  master总计: {total}家")

print("\n" + "="*55)
print("📦 CRM数据库统计")
print("="*55)
conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM customers")
print(f"  customers: {c.fetchone()[0]}家")
c.execute("SELECT industry, COUNT(*) FROM customers GROUP BY industry ORDER BY COUNT(*) DESC")
for r in c.fetchall():
    print(f"    {r[0]}: {r[1]}家")
c.execute("SELECT COUNT(*) FROM industry_cards")
print(f"  industry_cards: {c.fetchone()[0]}条")
conn.close()