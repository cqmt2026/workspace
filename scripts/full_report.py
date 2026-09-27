# -*- coding: utf-8 -*-
import sqlite3, json

db = r'F:\market_data.db'
conn = sqlite3.connect(db)
cursor = conn.cursor()

# 查持仓相关表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print('所有表:', tables)

# 查daily_k最新数据日期
cursor.execute("SELECT MAX(date) FROM daily_k")
latest = cursor.fetchone()[0]
print(f'最新日线日期: {latest}')

# 查今日涨跌
cursor.execute("""
    SELECT code, close, volume 
    FROM daily_k 
    WHERE date = ?
    ORDER BY close DESC
    LIMIT 10
""", (latest,))
print('\n今日涨幅Top10:')
for r in cursor.fetchall():
    print(f'  {r}')

conn.close()

# 读ML快照
p = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ml_snapshots\ml_candidates_20260903.json'
with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'\n=== ML筛选结果 ===')
print(f'日期: {data["date"]}')
print(f'总数: {data["total"]}')
print(f'ML>50%: {data["ml_prob_above_50"]}只')
print(f'ML>55%: {data["ml_prob_above_55"]}只')
print(f'ML>60%: {data["ml_prob_above_60"]}只')

high = [r for r in data['records'] if r['ml_prob'] > 0.50]
high = sorted(high, key=lambda x: -x['ml_prob'])
print(f'\nML>50% 共{len(high)}只:')
for r in high:
    print(f"  {r['code']} {r['name']} ML:{r['ml_prob']:.3f} 涨幅:{r['chg_pct']:+.2f}% 换手:{r['turnover']:.2f}% 量比:{r['vol_ratio']:.2f} 综合分:{r['score']:.1f}")
