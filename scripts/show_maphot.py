# -*- coding: utf-8 -*-
import json
import sys

p = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ml_snapshots\ml_candidates_20260903.json'
with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"日期: {data['date']}")
print(f"总数: {data['total']}")
print(f"ML>50%: {data['ml_prob_above_50']}")
print(f"ML>55%: {data['ml_prob_above_55']}")
print(f"ML>60%: {data['ml_prob_above_60']}")
print()

high = [r for r in data['records'] if r['ml_prob'] > 0.50]
print(f"ML>50% 共{len(high)}只:")
for r in sorted(high, key=lambda x: -x['ml_prob'])[:10]:
    print(f"  {r['code']} {r['name']} ML:{r['ml_prob']:.3f} 涨幅:{r['chg_pct']:.2f}% 换手:{r['turnover']:.2f}% 量比:{r['vol_ratio']:.2f} 分:{r['score']:.1f}")
