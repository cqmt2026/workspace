# -*- coding: utf-8 -*-
"""收盘RPS快速报告 - 2026-06-22"""
import json, os, sqlite3
from datetime import datetime, timedelta

OUT = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data'
DB = r'F:\market_data.db'
today = '20260622'

def load_rps(fname):
    path = os.path.join(OUT, fname)
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return json.load(f)

rps5 = load_rps(f'rps_5d_{today}.json')
rps10 = load_rps(f'rps_10d_{today}.json')
rps20 = load_rps(f'rps_20d_{today}.json')
rps60 = load_rps(f'rps_60d_{today}.json')

def get_bottom_stocks(n=10):
    """从DB查询今日涨幅最低的股票"""
    today_fmt = f'{today[:4]}-{today[4:6]}-{today[6:]}'
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(f"""
        SELECT t.code, t.close, y.close as prev_close
        FROM daily_k t
        LEFT JOIN daily_k y ON t.code = y.code AND y.date = (
            SELECT MAX(date) FROM daily_k WHERE date < t.date AND code = t.code
        )
        WHERE t.date = ? AND t.close > 0 AND y.close > 0
        ORDER BY (t.close - y.close) * 1.0 / y.close ASC
        LIMIT ?
    """, (today_fmt, n))
    rows = cur.fetchall()
    conn.close()
    return [{'code': r[0], 'return': round((r[1]-r[2])/r[2]*100, 2)} for r in rows]

print('=' * 65)
print(f'  收盘RPS报告  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
print('=' * 65)

period_map = [
    ('5日', rps5, 'rps_5d', 'return_5d'), 
    ('10日', rps10, 'rps_10d', 'return_10d'),
    ('20日', rps20, 'rps_20d', 'return_20d'), 
    ('60日', rps60, 'rps_60d', 'return_60d')
]
for period, data, rps_key, ret_key in period_map:
    stocks = data.get('top_stocks', [])
    print(f'\n--- RPS {period} Top15 (共{data.get("total_stocks","?")}只) ---')
    for i, s in enumerate(stocks[:15], 1):
        code = s.get('code','')
        rps = s.get(rps_key, 0)
        ret = s.get(ret_key, 0)
        print(f'  {i:2d}. {code:<12} RPS={rps:.1f} 涨幅={ret:+.2f}%')

print()
print('--- RPS 5日 Bottom10 (弱势股) ---')
bottom = get_bottom_stocks(10)
for i, s in enumerate(bottom, 1):
    print(f'  {i:2d}. {s["code"]:<12} 涨幅={s["return"]:+.2f}%')

# Save compact report
report = {
    'date': today,
    'generated': datetime.now().isoformat(),
    'rps5_top15': [{'code': s['code'], 'rps': s.get('rps_5d',0), 'return': s.get('return_5d',0)} for s in rps5.get('top_stocks',[])[:15]],
    'rps10_top15': [{'code': s['code'], 'rps': s.get('rps_10d',0), 'return': s.get('return_10d',0)} for s in rps10.get('top_stocks',[])[:15]],
    'rps20_top15': [{'code': s['code'], 'rps': s.get('rps_20d',0), 'return': s.get('return_20d',0)} for s in rps20.get('top_stocks',[])[:15]],
    'rps60_top15': [{'code': s['code'], 'rps': s.get('rps_60d',0), 'return': s.get('return_60d',0)} for s in rps60.get('top_stocks',[])[:15]],
    'rps5_bottom10': bottom,
}
out_path = os.path.join(OUT, f'rps_closing_{today}.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print(f'\n报告已保存: {out_path}')
