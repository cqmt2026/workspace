import json

d = json.load(open(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ml_snapshots\ml_candidates_20260831.json'))
print(f'=== 2026-08-31 尾盘精选扫描结果 ===')
print(f'总数: {d["total"]}')
print(f'ML>50%: {d["ml_prob_above_50"]}')
print(f'ML>55%: {d["ml_prob_above_55"]}')
print(f'ML>60%: {d["ml_prob_above_60"]}')
print()
print('=== ML>60% 高置信候选 ===')
for r in d['records']:
    if r['ml_prob'] > 0.6:
        print(f'  {r["code"]} {r["name"]} ML:{r["ml_prob"]*100:.1f}% 涨幅:{r["chg_pct"]:+.2f}% 换手:{r["turnover"]}% 量比:{r["vol_ratio"]}')
print()
print('=== ML 50%-60% 中等候选 ===')
for r in d['records']:
    if 0.5 <= r['ml_prob'] <= 0.6:
        print(f'  {r["code"]} {r["name"]} ML:{r["ml_prob"]*100:.1f}% 涨幅:{r["chg_pct"]:+.2f}% 换手:{r["turnover"]}% 量比:{r["vol_ratio"]}')
print()
print('=== Top 5 综合评分 ===')
for r in d['records'][:5]:
    print(f'  {r["code"]} {r["name"]} 评分:{r["score"]:.1f} ML:{r["ml_prob"]*100:.1f}% 涨幅:{r["chg_pct"]:+.2f}%')
