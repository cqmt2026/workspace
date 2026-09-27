import json

with open(r"C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ml_snapshots\ml_candidates_20260817.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print(f"日期: {d['date']}")
print(f"总候选: {d['total']} 只")
print(f"ML>50%: {d['ml_prob_above_50']} 只")
print(f"ML>55%: {d['ml_prob_above_55']} 只")
print(f"ML>60%: {d['ml_prob_above_60']} 只")
print()
print("=== ML>60% 高置信候选 ===")
for r in d["records"]:
    if r["ml_prob"] > 0.6:
        print(f"  {r['code']} {r['name']} ML:{r['ml_prob']:.3f} 涨幅:{r['chg_pct']}% 换手:{r['turnover']}% 量比:{r['vol_ratio']} 分:{r['score']:.1f}")

print()
print("=== ML 50-60% ===")
for r in d["records"]:
    if 0.5 <= r["ml_prob"] <= 0.6:
        print(f"  {r['code']} {r['name']} ML:{r['ml_prob']:.3f} 涨幅:{r['chg_pct']}% 换手:{r['turnover']}% 量比:{r['vol_ratio']} 分:{r['score']:.1f}")

print()
print("=== Top 10 综合评分 ===")
for r in d["records"][:10]:
    print(f"  {r['code']} {r['name']} ML:{r['ml_prob']:.3f} 涨幅:{r['chg_pct']}% 换手:{r['turnover']}% 量比:{r['vol_ratio']} 分:{r['score']:.1f}")
