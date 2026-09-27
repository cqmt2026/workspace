"""
H-014 威科夫缩量回调 + MA5均线出场（快速验证）
"""

import sqlite3, pandas as pd, numpy as np, sys
DB = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\market_data.db'
CODES_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ta_backtest\sample_500.txt'
OUT = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ta_backtest'
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts')
from significance_test import run as sig_test

codes = open(CODES_FILE).read().strip().split('\n')
conn = sqlite3.connect(DB)
csi300 = pd.read_sql(
    "SELECT date, close FROM daily_k WHERE code='sh.000300' AND date>='2019-01-01' ORDER BY date", conn)
csi300['date'] = pd.to_datetime(csi300['date'])
csi300 = csi300.sort_values('date').reset_index(drop=True)
csi300['ma5'] = csi300['close'].rolling(5).mean()
csi300['ma20'] = csi300['close'].rolling(20).mean()
csi_dict = {d: (r[0], r[1]) for d, r in zip(csi300['date'], csi300[['ma5','ma20']].values)}
conn.close()

cs = ','.join(["'" + c + "'" for c in codes])
conn = sqlite3.connect(DB)
df = pd.read_sql(
    "SELECT code, date, close, volume FROM daily_k WHERE code IN (" + cs + ") AND date>='2019-01-01' ORDER BY code, date", conn)
conn.close()
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code','date']).reset_index(drop=True)

all_rows = []
for code, grp in df.groupby('code'):
    g = grp.sort_values('date').copy()
    g['ma5'] = g['close'].rolling(5).mean()
    g['ma10'] = g['close'].rolling(10).mean()
    g['ma20'] = g['close'].rolling(20).mean()
    g['vol5'] = g['volume'].rolling(5).mean()
    g['ret1'] = g['close'].pct_change(1)
    g['ret5'] = g['close'].pct_change(5)
    g['ret20'] = g['close'].pct_change(20)
    all_rows.append(g)
df = pd.concat(all_rows, ignore_index=True)
df = df[df['date'] >= pd.Timestamp('2019-06-01')].copy()

all_dates = sorted(df['date'].unique())
sig_dates = all_dates[::5]

trades = []
last_map = {}

for sig_date in sig_dates:
    csi = csi_dict.get(sig_date)
    if csi is None or csi[0] <= csi[1]:
        continue

    day_df = df[df['date'] == sig_date].copy()
    day_df = day_df[
        (day_df['close'] > 0) &
        day_df['ma5'].notna() & day_df['ma20'].notna() &
        day_df['vol5'].notna() & (day_df['vol5'] > 0) &
        day_df['ret20'].notna()
    ]

    # MA5>MA20 且 前期涨幅>5%
    cand = day_df[(day_df['ma5'] > day_df['ma20']) & (day_df['ret20'] > 0.05)]
    if len(cand) == 0:
        continue

    # 选RSI最低的2只
    rsi_vals = {}
    for idx, r in cand.iterrows():
        ret_series = df[(df['code'] == r['code']) & (df['date'] <= sig_date)].tail(14)['close'].pct_change()
        gains = ret_series.clip(lower=0).mean()
        losses = (-ret_series.clip(upper=0)).mean()
        rs = gains / (losses + 0.001)
        rsi_vals[idx] = 100 - (100 / (1 + rs))
    cand = cand.copy()
    cand['rsi'] = cand.index.map(rsi_vals)
    top2 = cand.nsmallest(2, 'rsi')

    for _, row in top2.iterrows():
        code = row['code']
        last_t = last_map.get(code)
        if last_t and (sig_date - last_t).days < 15:
            continue

        entry_price = float(row['close'])
        stop_loss = entry_price * 0.97

        stock_post = df[(df['code'] == code) & (df['date'] > sig_date)].sort_values('date')
        if len(stock_post) < 3:
            continue

        exit_dt = None
        exit_px = None
        exit_rs = None
        max_ret = 0.0

        for i, (_, frow) in enumerate(stock_post.iterrows()):
            days = i + 1
            price = float(frow['close'])
            ret = (price - entry_price) / entry_price
            ma5_v = float(frow['ma5']) if not pd.isna(frow['ma5']) else None
            ma10_v = float(frow['ma10']) if not pd.isna(frow['ma10']) else None

            if ret > max_ret:
                max_ret = ret

            if price < stop_loss:
                exit_dt = frow['date']
                exit_px = price
                exit_rs = 'stop_3pct'
                break
            if ma5_v and ma10_v and ma5_v < ma10_v:
                exit_dt = frow['date']
                exit_px = price
                exit_rs = 'profit_ma5_cross'
                break
            if days >= 5:
                exit_dt = frow['date']
                exit_px = price
                exit_rs = 'expire_5d'
                break

        if exit_dt and exit_px:
            last_map[code] = exit_dt
            trades.append({
                'code': code,
                'sig_date': str(sig_date.date()),
                'entry_date': str(sig_date.date()),
                'exit_date': str(exit_dt.date()),
                'return': (exit_px - entry_price) / entry_price,
                'exit_reason': exit_rs,
                'hold_days': (exit_dt - sig_date).days,
                'max_return': max_ret,
            })

trades_df = pd.DataFrame(trades)
rets = trades_df['return'].values

print('H-014 结果:')
print('  交易数: %d' % len(trades))
if len(trades) > 0:
    print('  胜率: %.1f%%' % ((rets > 0).mean() * 100))
    print('  平均收益: %+.2f%%' % (rets.mean() * 100))
    print('  最大盈利: %+.2f%%' % (rets.max() * 100))
    print('  最大亏损: %+.2f%%' % (rets.min() * 100))
    sig = sig_test([{'return': float(r)} for r in rets], name='H-014')
    print('  显著性: %s' % sig.get('conclusion', '?'))
    print('  出场:')
    for reason, cnt in trades_df['exit_reason'].value_counts().items():
        print('    %s: %d (%.1f%%)' % (reason, cnt, cnt/len(trades)*100))
    wins = rets[rets > 0]
    losses = rets[rets < 0]
    if len(wins) > 0 and len(losses) > 0:
        print('  盈亏比: %.2f' % (wins.mean() / abs(losses.mean())))
    print('  持有天数: mean=%.1f' % trades_df['hold_days'].mean())
trades_df.to_csv(OUT + '/H014_trades.csv', index=False)
print('DONE')