# -*- coding: utf-8 -*-
"""生成IC滚动报告"""
import sys, os, sqlite3, json
import numpy as np
from datetime import datetime
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')

STORE_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\factors.db'
OUTPUT_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data'
os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = sqlite3.connect(STORE_PATH)

# Get all IC records
rows = conn.execute(
    "SELECT date, factor_name, ic, p_value, n_stocks FROM ic_history ORDER BY date DESC, factor_name"
).fetchall()
conn.close()

print(f"总IC记录数: {len(rows)}")

# Group by date
from collections import defaultdict
by_date = defaultdict(list)
for r in rows:
    by_date[r[0]].append({'factor': r[1], 'ic': r[2], 'p_value': r[3], 'n_stocks': r[4]})

sorted_dates = sorted(by_date.keys(), reverse=True)
print(f"日期范围: {sorted_dates[-1]} ~ {sorted_dates[0]}")

# 60天滚动统计
recent_60 = sorted_dates[:60]
print(f"近60天: {recent_60[-1]} ~ {recent_60[0]}")

# Factor stats over rolling window
factor_stats = {}
for date in recent_60:
    for rec in by_date[date]:
        fn = rec['factor']
        if fn not in factor_stats:
            factor_stats[fn] = []
        factor_stats[fn].append(rec['ic'])

print(f"\n因子60日IC统计:")
print(f"{'因子':<25} {'mean_ic':>8} {'ic_ir':>8} {'pos%':>6} {'n':>4} {'status':>8}")
print("-" * 65)

status_updates = []
for fn in sorted(factor_stats.keys()):
    ics = factor_stats[fn][:60]  # most recent 60
    mean_ic = float(np.mean(ics))
    std_ic = float(np.std(ics))
    ic_ir = mean_ic / std_ic if std_ic > 0 else 0.0
    positive_ratio = sum(1 for x in ics if x > 0) / len(ics)
    n = len(ics)
    status = 'active'
    if abs(mean_ic) < 0.02 and n >= 10:
        status = 'eliminated'
    
    print(f"{fn:<25} {mean_ic:>8.4f} {ic_ir:>8.4f} {positive_ratio:>6.1%} {n:>4} {status:>8}")
    
    status_updates.append({
        'factor_name': fn, 'mean_ic': mean_ic, 'ic_ir': ic_ir,
        'positive_ratio': positive_ratio, 'n_days': n, 'status': status
    })

# Save factor status
conn = sqlite3.connect(STORE_PATH)
for s in status_updates:
    conn.execute("""
        INSERT INTO factor_status (factor_name, category, mean_ic, ic_ir, positive_ratio, n_days, status, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(factor_name) DO UPDATE SET
            mean_ic = excluded.mean_ic, ic_ir = excluded.ic_ir,
            positive_ratio = excluded.positive_ratio, n_days = excluded.n_days,
            status = excluded.status, last_updated = excluded.last_updated
    """, (s['factor_name'], 'technical', s['mean_ic'], s['ic_ir'], s['positive_ratio'], s['n_days'], s['status'], datetime.now().strftime('%Y-%m-%d')))
conn.commit()
conn.close()

# Generate report JSON
report = {
    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'date_range': {'start': sorted_dates[-1], 'end': sorted_dates[0]},
    'total_records': len(rows),
    'recent_60_days': recent_60[-1] if recent_60 else None,
    'factor_stats_60d': {s['factor_name']: {
        'mean_ic': round(s['mean_ic'], 4),
        'ic_ir': round(s['ic_ir'], 4),
        'positive_ratio': round(s['positive_ratio'], 4),
        'n_days': s['n_days'],
        'status': s['status']
    } for s in sorted(status_updates, key=lambda x: abs(x['mean_ic']), reverse=True)},
    'daily_ic': {d: [{'factor': r['factor'], 'ic': round(r['ic'], 4), 'p_value': round(r['p_value'], 4) if r['p_value'] else None} for r in by_date[d]] for d in sorted_dates[:30]}
}

output_path = os.path.join(OUTPUT_DIR, f'ic_report_60d_{datetime.now().strftime("%Y%m%d")}.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f"\n报告已保存: {output_path}")

# Print top factors
print(f"\nTop 5 IC因子 (绝对值):")
sorted_factors = sorted(status_updates, key=lambda x: abs(x['mean_ic']), reverse=True)
for i, s in enumerate(sorted_factors[:5]):
    print(f"  {i+1}. {s['factor_name']}: mean_ic={s['mean_ic']:.4f}, icir={s['ic_ir']:.4f}, status={s['status']}")

print(f"\nBottom 5 IC因子 (绝对值):")
for i, s in enumerate(sorted_factors[-5:]):
    print(f"  {i+1}. {s['factor_name']}: mean_ic={s['mean_ic']:.4f}, icir={s['ic_ir']:.4f}, status={s['status']}")
