import sys, json, sqlite3
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Check the signal for 601888
db = r'F:\market_data.db'
code = '601888'
db_code = f'sh.{code}'

conn = sqlite3.connect(db)
rows = conn.execute(
    'SELECT date, close, open, volume FROM daily_k WHERE code=? AND date<=? ORDER BY date DESC LIMIT 70',
    (db_code, '2026-08-21')
).fetchall()
conn.close()

if len(rows) < 10:
    print('Insufficient data')
else:
    closes = [r[1] for r in reversed(rows)]
    print(f'Total rows: {len(rows)}')
    print(f'60日涨跌: {(closes[-1]-closes[0])/closes[0]*100:.1f}%')
    volumes = [r[3] for r in reversed(rows)]
    avg_vol = sum(volumes[-60:])/60
    max_vol = max(volumes[-60:])
    print(f'量比: {max_vol/avg_vol:.2f}' if avg_vol > 0 else 'N/A')
    print(f'最新5日收盘价: {[round(c,2) for c in closes[-5:]]}')
