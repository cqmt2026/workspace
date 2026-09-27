import sqlite3
import time
conn = sqlite3.connect(r'F:/market_data.db')
t0 = time.time()
# Test the actual query used in compute_technical
codes = conn.execute("SELECT code FROM daily_k WHERE date='2026-08-21' AND code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%' AND code NOT LIKE 'sh.9%' AND close>0 AND volume>0").fetchall()
codes = [c[0] for c in codes]
print(f"Got {len(codes)} codes in {time.time()-t0:.1f}s")
t1 = time.time()
ph = ','.join(['?'] * 500)
rows = conn.execute(
    "SELECT code, date, close, volume, high, low FROM daily_k "
    f"WHERE code IN ({ph}) AND date>='2026-01-01' AND date<='2026-08-21' "
    "ORDER BY code, date ASC",
    codes[:500] + ['2026-08-21']
).fetchall()
print(f"Batch query 1: {len(rows)} rows in {time.time()-t1:.1f}s")
t2 = time.time()
rows2 = conn.execute(
    "SELECT code, date, close, volume, high, low FROM daily_k "
    f"WHERE code IN ({ph}) AND date>='2026-01-01' AND date<='2026-08-21' "
    "ORDER BY code, date ASC",
    codes[500:1000] + ['2026-08-21']
).fetchall()
print(f"Batch query 2: {len(rows2)} rows in {time.time()-t2:.1f}s")
conn.close()
print(f"Total: {time.time()-t0:.1f}s")
