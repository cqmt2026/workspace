# -*- coding: utf-8 -*-
"""Recompute factor_status from existing ic_history in factors.db"""
import sqlite3
import numpy as np

path = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\factors.db'
conn = sqlite3.connect(path)

# Get categories from factor_status
cats = dict(conn.execute(
    'SELECT factor_name, category FROM factor_status'
).fetchall())

# Group by factor
by_factor = {}
for date, fname, ic, pval, n in conn.execute(
    'SELECT date, factor_name, ic, p_value, n_stocks FROM ic_history ORDER BY date'
).fetchall():
    by_factor.setdefault(fname, []).append((date, ic, pval, n))

print(f'Factoring {len(by_factor)} factors from {len(set(r[0] for r in conn.execute("SELECT date FROM ic_history").fetchall()))} dates')
print()
print(f'{"factor":<20} {"n_days":>7} {"mean_ic":>9} {"ir":>7} {"pos_ratio":>11} {"status":<12}')
print('-' * 66)

active = []
inverse = []
watch = []
eliminated = []
cold = []

for fname, recs in sorted(by_factor.items()):
    ics = [r[1] for r in recs]
    days = len(ics)
    mean_ic = float(np.mean(ics))
    std_ic = float(np.std(ics, ddof=1)) if days > 1 else 0.0
    ic_ir = mean_ic / std_ic if (std_ic > 0.001 and days >= 5) else 0.0
    pos_ratio = sum(1 for x in ics if x > 0) / len(ics)
    sig_ratio = sum(1 for r in recs if r[2] < 0.05) / max(len(ics), 1)

    if days < 5:
        st = 'cold'
        cold.append(fname)
    elif abs(mean_ic) < 0.005 or sig_ratio < 0.2:
        st = 'eliminated'
        eliminated.append(fname)
    elif mean_ic < -0.02 and sig_ratio > 0.2:
        st = 'inverse'
        inverse.append(fname)
    elif mean_ic >= 0.015 and sig_ratio > 0.2:
        st = 'active'
        active.append(fname)
    else:
        st = 'watch'
        watch.append(fname)

    cat = cats.get(fname, 'technical')
    conn.execute("""
        INSERT OR REPLACE INTO factor_status
        (factor_name, category, mean_ic, ic_ir, positive_ratio, n_days, status, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (fname, cat, mean_ic, ic_ir, pos_ratio, days, st))

    print(f'{fname:<20} {days:>7} {mean_ic:>+9.4f} {ic_ir:>+7.2f} {pos_ratio:>11.2f} {st:<12}')

conn.commit()
conn.close()

print()
print(f'=== Summary ===')
print(f'  Active:    {len(active)} -> {", ".join(active)}')
print(f'  Inverse:   {len(inverse)} -> {", ".join(inverse)}')
print(f'  Watch:     {len(watch)} -> {", ".join(watch)}')
print(f'  Cold:      {len(cold)} -> {", ".join(cold)}')
print(f'  Eliminated:{len(eliminated)} -> {", ".join(eliminated)}')
print()
print(f'Factor status table updated from {sum(1 for r in by_factor)} factors.')
