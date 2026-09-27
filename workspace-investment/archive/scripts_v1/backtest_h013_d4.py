"""
H-013 方向4：买入从涨停后第3天开始（跳过前2天）
其他：lu_low止损 + MA10止盈 + 15日
"""

import sqlite3
import pandas as pd
import numpy as np
import sys

DB = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\market_data.db'
CODES_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ta_backtest\sample_500.txt'
OUT = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ta_backtest'
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts')
from significance_test import run as sig_test

print("=" * 60)
print("H-013 方向4：涨停后第3天起可买 / lu_low止损 / MA10止盈")
print("=" * 60)

codes = open(CODES_FILE).read().strip().split('\n')
print("样本: %d只" % len(codes))

conn = sqlite3.connect(DB)
csi300 = pd.read_sql("SELECT date, close FROM daily_k WHERE code='sh.000300' AND date>='2019-01-01' ORDER BY date", conn)
csi300['date'] = pd.to_datetime(csi300['date'])
csi300 = csi300.sort_values('date').reset_index(drop=True)
csi300['ma5'] = csi300['close'].rolling(5).mean()
csi300['ma20'] = csi300['close'].rolling(20).mean()
csi_dict = {d: (r[0], r[1]) for d, r in zip(csi300['date'], csi300[['ma5','ma20']].values)}
conn.close()

cs = ','.join(["'" + c + "'" for c in codes])
conn = sqlite3.connect(DB)
df = pd.read_sql("SELECT code, date, open, high, low, close, volume FROM daily_k WHERE code IN (%s) AND date>='2019-01-01' ORDER BY code, date" % cs, conn)
conn.close()
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date']).reset_index(drop=True)

print("计算指标...")
all_rows = []
for code, grp in df.groupby('code'):
    g = grp.sort_values('date').copy()
    g['ma5'] = g['close'].rolling(5).mean()
    g['ma10'] = g['close'].rolling(10).mean()
    g['vol5'] = g['volume'].rolling(5).mean()
    g['ret1'] = g['close'].pct_change(1)
    g['prev_close'] = g['close'].shift(1)
    all_rows.append(g)
df = pd.concat(all_rows, ignore_index=True)
df = df[df['date'] >= pd.Timestamp('2019-06-01')].copy()
print("有效数据: %d行" % len(df))

print("按股票处理...")
trades = []

for code, grp in df.groupby('code'):
    g = grp.sort_values('date').copy()
    vals = g[['date','open','high','low','close','volume','ma5','ma10','vol5','ret1','prev_close']].values
    
    for i in range(30, len(vals)):
        date, open_, high, low, close, volume, ma5, ma10, vol5, ret1, prev_close = vals[i]
        if prev_close > 0 and close / prev_close >= 1.095:
            p30 = vals[i-30][4] if i >= 30 else vals[0][4]
            if p30 > 0 and (prev_close - p30) / p30 < 0.50:
                lu_date = date
                lu_low = low
                lu_close = close
                
                if i + 12 >= len(vals):  # 方向4：需要更多后续天数
                    continue
                
                max_since = lu_close
                
                # 方向4：从第3天开始（j = i+3起）
                for j in range(i + 3, min(i + 11, len(vals))):
                    buy_date, b_open, b_high, b_low, b_close, b_vol, b_ma5, b_ma10, b_vol5, b_ret1, b_prev_close = vals[j]
                    
                    if b_vol5 is None or b_vol5 <= 0 or b_ret1 is None:
                        continue
                    
                    if b_close > max_since:
                        max_since = b_close
                    
                    if b_close < lu_low:
                        continue
                    
                    pullback = (max_since - b_close) / max_since if max_since > 0 else 0
                    if pullback < 0.05 or pullback > 0.25:
                        continue
                    
                    if b_ret1 <= 0 or b_vol <= b_vol5 * 1.5:
                        continue
                    
                    csi = csi_dict.get(buy_date)
                    if csi is None or csi[0] <= csi[1]:
                        continue
                    
                    entry_price = b_close
                    stop_loss = entry_price * 0.97
                    
                    exit_dt = None
                    exit_px = None
                    exit_rs = None
                    max_ret = 0.0
                    
                    for k in range(j + 1, len(vals)):
                        f_date, f_open, f_high, f_low, f_close, f_vol, f_ma5, f_ma10, f_vol5, f_ret1, f_prev_close = vals[k]
                        days = k - j
                        ret = (f_close - entry_price) / entry_price
                        
                        if ret > max_ret:
                            max_ret = ret
                        
                        if f_close < lu_low:
                            exit_dt = f_date
                            exit_px = f_close
                            exit_rs = 'stop_lu_low'
                            break
                        if f_close < stop_loss:
                            exit_dt = f_date
                            exit_px = f_close
                            exit_rs = 'stop_3pct'
                            break
                        if f_ma5 and f_ma10 and f_ma5 < f_ma10:
                            exit_dt = f_date
                            exit_px = f_close
                            exit_rs = 'profit_ma10_cross'
                            break
                        if days >= 15:
                            exit_dt = f_date
                            exit_px = f_close
                            exit_rs = 'expire_15d'
                            break
                    
                    if exit_dt and exit_px and entry_price > 0:
                        final_ret = (exit_px - entry_price) / entry_price
                        trades.append({
                            'code': code,
                            'sig_date': str(pd.Timestamp(buy_date).date()),
                            'exit_date': str(pd.Timestamp(exit_dt).date()),
                            'return': final_ret,
                            'exit_reason': exit_rs,
                            'hold_days': (pd.Timestamp(exit_dt) - pd.Timestamp(buy_date)).days,
                            'max_return': max_ret,
                            'pullback': pullback
                        })

print("交易: %d笔" % len(trades))
if len(trades) == 0:
    print("无交易")
    sys.exit(0)

trades_df = pd.DataFrame(trades)

def get_csi(s, e):
    d1 = csi300[csi300['date'] == pd.Timestamp(s)]
    d2 = csi300[csi300['date'] == pd.Timestamp(e)]
    if len(d1) == 0 or len(d2) == 0: return None
    return (float(d2['close'].values[0]) - float(d1['close'].values[0])) / float(d1['close'].values[0])

trades_df['csi_return'] = trades_df.apply(lambda r: get_csi(r['sig_date'], r['exit_date']), axis=1)
trades_df['excess_return'] = trades_df['return'] - trades_df['csi_return']

rets = trades_df['return'].values
excess = trades_df['excess_return'].dropna().values
win = float((rets > 0).mean())
avg = float(rets.mean())
avg_ex = float(excess.mean()) if len(excess) > 0 else 0

print("\n" + "=" * 50)
print("方向4结果")
print("=" * 50)
print("交易数: %d" % len(trades))
print("胜率: %.1f%%" % (win * 100))
print("平均收益: %+.2f%%" % (avg * 100))
print("平均超额收益: %+.2f%%" % (avg_ex * 100))
print("最大盈利: %+.2f%%" % (rets.max() * 100))
print("最大亏损: %+.2f%%" % (rets.min() * 100))

sig = sig_test([{'return': float(r)} for r in rets], name='H-013-D4')
print("显著性: %s" % sig.get('conclusion', '?'))

print("\n出场原因:")
for reason, cnt in trades_df['exit_reason'].value_counts().items():
    print("  %s: %d (%.1f%%)" % (reason, cnt, cnt/len(trades)*100))

wins = rets[rets > 0]
losses = rets[rets < 0]
if len(wins) > 0 and len(losses) > 0:
    print("盈亏比: %.2f" % (wins.mean() / abs(losses.mean())))
print("持有天数: mean=%.1f" % trades_df['hold_days'].mean())

trades_df.to_csv(OUT + '/H013_D4_trades.csv', index=False)
print("\nDONE")