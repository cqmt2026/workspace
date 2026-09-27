"""
H-015 布林带收口 + MACD金叉0轴以上
布林带收口 = 缩量整理
MACD在0轴上方金叉 = 主力启动
"""

import sqlite3, pandas as pd, numpy as np, sys

DB = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\market_data.db'
CODES_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ta_backtest\sample_500.txt'
OUT = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ta_backtest'
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts')
from significance_test import run as sig_test

print("H-015 布林带收口+MACD金叉0轴上")

codes = open(CODES_FILE).read().strip().split('\n')
conn = sqlite3.connect(DB)
csi300 = pd.read_sql(
    "SELECT date, close FROM daily_k WHERE code='sh.000300' AND date>='2019-01-01' ORDER BY date", conn)
csi300['date'] = pd.to_datetime(csi300['date'])
csi300 = csi300.sort_values('date').reset_index(drop=True)
csi300['ma5'] = csi300['close'].rolling(5).mean()
csi300['ma20'] = csi300['close'].rolling(20).mean()
csi_dict = {d: (r[0], r[1]) for d, r in
    zip(csi300['date'], csi300[['ma5','ma20']].values)}
conn.close()

cs = ','.join(["'" + c + "'" for c in codes])
conn = sqlite3.connect(DB)
df = pd.read_sql(
    "SELECT code, date, close, volume FROM daily_k "
    "WHERE code IN (" + cs + ") AND date>='2019-01-01' ORDER BY code, date", conn)
conn.close()
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code','date']).reset_index(drop=True)

# 指标
rows = []
for code, grp in df.groupby('code'):
    g = grp.sort_values('date').copy()
    g['ma5'] = g['close'].rolling(5).mean()
    g['ma10'] = g['close'].rolling(10).mean()
    g['ma20'] = g['close'].rolling(20).mean()
    g['std20'] = g['close'].rolling(20).std()
    g['upper'] = g['ma20'] + 2 * g['std20']
    g['lower'] = g['ma20'] - 2 * g['std20']
    g['vol5'] = g['volume'].rolling(5).mean()
    g['vol20'] = g['volume'].rolling(20).mean()
    # MACD(12,26,9)
    ema12 = g['close'].ewm(span=12, adjust=False).mean()
    ema26 = g['close'].ewm(span=26, adjust=False).mean()
    g['macd'] = ema12 - ema26
    g['macd_signal'] = g['macd'].ewm(span=9, adjust=False).mean()
    g['macd_hist'] = g['macd'] - g['macd_signal']
    g['prev_macd_hist'] = g['macd_hist'].shift(1)
    # ret
    g['ret5'] = g['close'].pct_change(5)
    rows.append(g)
df = pd.concat(rows, ignore_index=True)
df = df[df['date'] >= pd.Timestamp('2019-06-01')].copy()

# 布林带宽度
df['bb_width'] = (df['upper'] - df['lower']) / df['ma20']
df['bb_width_ma10'] = df.groupby('code')['bb_width'].transform(lambda x: x.rolling(10).mean())

all_dates = sorted(df['date'].unique())
sig_dates = all_dates[::5]

trades = []
last_trade = {}

for sig_date in sig_dates:
    csi = csi_dict.get(sig_date)
    if csi is None or csi[0] <= csi[1]:
        continue

    day = df[df['date'] == sig_date].copy()
    day = day[(day['close'] > 0) & day['bb_width'].notna() & day['bb_width_ma10'].notna() &
              day['macd_hist'].notna() & day['prev_macd_hist'].notna() &
              day['ma5'].notna() & day['ma20'].notna() &
              day['vol5'].notna() & (day['vol5'] > 0)]
    if len(day) == 0:
        continue

    # 条件1：布林带收口（宽度<10日均值×0.5）
    cond1 = day['bb_width'] < day['bb_width_ma10'] * 0.5
    # 条件2：MACD在0轴上方金叉（hist由负转正）
    cond2 = (day['macd_hist'] > 0) & (day['prev_macd_hist'] < 0)
    # 条件3：个股上升趋势
    cond3 = day['ma5'] > day['ma20']

    cand = day[cond1 & cond2 & cond3]
    if len(cand) == 0:
        continue

    for _, row in cand.nlargest(2, 'macd_hist').iterrows():
        code = row['code']
        if last_trade.get(code) and (sig_date - last_trade[code]).days < 15:
            continue

        entry_price = float(row['close'])
        entry_date = sig_date

        stock = df[(df['code'] == code) & (df['date'] > sig_date)].sort_values('date')
        if len(stock) < 3:
            continue

        exit_date = None
        exit_price = None
        exit_reason = None
        max_ret = 0.0

        for i, (_, frow) in enumerate(stock.iterrows()):
            days = i + 1
            price = float(frow['close'])
            ret = (price - entry_price) / entry_price
            macd_h = float(frow['macd_hist']) if not pd.isna(frow['macd_hist']) else 0
            prev_macd = float(frow['prev_macd_hist']) if not pd.isna(frow['prev_macd_hist']) else 0

            if ret > max_ret:
                max_ret = ret

            # MACD死叉
            if prev_macd > 0 and macd_h < 0:
                exit_date = frow['date']
                exit_price = price
                exit_reason = 'macd_dead_cross'
                break

            # 持有20日到期
            if days >= 20:
                exit_date = frow['date']
                exit_price = price
                exit_reason = 'expire_20d'
                break

        if exit_date and exit_price:
            last_trade[code] = exit_date
            final_ret = (exit_price - entry_price) / entry_price
            trades.append({
                'code': code,
                'entry_date': str(entry_date.date()),
                'exit_date': str(exit_date.date()),
                'return': final_ret,
                'exit_reason': exit_reason,
                'hold_days': (exit_date - entry_date).days,
                'max_return': max_ret,
            })

print("交易: %d笔" % len(trades))

if len(trades) == 0:
    print("无交易")
    sys.exit(0)

trades_df = pd.DataFrame(trades)

def get_csi(s, e):
    d1 = csi300[csi300['date'] == pd.Timestamp(s)]
    d2 = csi300[csi300['date'] == pd.Timestamp(e)]
    if len(d1) == 0 or len(d2) == 0:
        return None
    return (float(d2['close'].values[0]) - float(d1['close'].values[0])) / float(d1['close'].values[0])

trades_df['csi_return'] = trades_df.apply(
    lambda r: get_csi(r['entry_date'], r['exit_date']), axis=1)
trades_df['excess_return'] = trades_df['return'] - trades_df['csi_return']

rets = trades_df['return'].values
excess = trades_df['excess_return'].dropna().values
win = float((rets > 0).mean())
avg = float(rets.mean())
avg_ex = float(excess.mean()) if len(excess) > 0 else 0

print("\nH-015 结果")
print("=" * 40)
print("交易数: %d" % len(trades))
print("胜率: %.1f%%" % (win * 100))
print("平均收益: %+.2f%%" % (avg * 100))
print("平均超额: %+.2f%%" % (avg_ex * 100))
print("最大盈利: %+.2f%%" % (rets.max() * 100))
print("最大亏损: %+.2f%%" % (rets.min() * 100))

sig = sig_test([{'return': float(r)} for r in rets], name='H-015')
print("显著性: %s" % sig.get('conclusion', '?'))

print("\n出场:")
for r, c in trades_df['exit_reason'].value_counts().items():
    print("  %s: %d (%.1f%%)" % (r, c, c/len(trades)*100))

wins = rets[rets > 0]
losses = rets[rets < 0]
if len(wins) > 0 and len(losses) > 0:
    print("盈亏比: %.2f" % (wins.mean() / abs(losses.mean())))
print("持有天数: mean=%.1f" % trades_df['hold_days'].mean())

trades_df.to_csv(OUT + '/H015_trades.csv', index=False)
print("DONE")