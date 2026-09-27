import sqlite3
conn = sqlite3.connect(r'F:/market_data.db')
print('max_date:', conn.execute('SELECT MAX(date) FROM daily_k').fetchone()[0])
print('count_20260821:', conn.execute("SELECT COUNT(*) FROM daily_k WHERE date='2026-08-21'").fetchone()[0])
print('codes_20260821:', len(conn.execute("SELECT code FROM daily_k WHERE date='2026-08-21' AND code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%' AND code NOT LIKE 'sh.9%' AND close>0 AND volume>0").fetchall()))
conn.close()
