"""
H-014 威科夫缩量回调 + 均线趋势（精简版）
每只股票最多每20天1个信号
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

print("H-014 威科夫缩量回调")

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
    "SELECT code, date, open, high, low, close, volume FROM daily_k "
    "WHERE code IN (%s) AND date>='2019-01-01' ORDER BY code, date" % cs, conn)
conn.close()
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date']).reset_index(drop=True)

all_rows = []
for code, grp in df.groupby('code'):
    g = grp.sort_values('date').copy()
    g['ma5'] = g['close'].rolling(5).mean()
    g['ma10'] = g['close'].rolling(10).mean()
    g['ma20'] = g['close'].rolling(20).mean()
    g['vol5'] = g['volume'].rolling(5).mean()
    g['vol10'] = g['volume'].rolling(10).mean()
    g['vol20'] = g['volume'].rolling(20).mean()
    g['ret1'] = g['close'].pct_change(1)
    g['ret5'] = g['close'].pct_change(5)
    g['ret20'] = g['close'].pct_change(20)
    all_rows.append(g)
df = pd.concat(all_rows, ignore_index=True)
df = df[df['date'] >= pd.Timestamp('2019-06-01')].copy()

trades = []
last_trade_date = {}  # 每只股票上次交易日期

for code, grp in df.groupby('code'):
    g = grp.sort_values('date').copy()
    vals = g[['date','close','volume','ma5','ma10','ma20','vol5','vol10','vol20','ret1','ret5','ret20']].values
    
    for i in range(25, len(vals) - 1):
        date, close, vol, ma5, ma10, ma20, vol5, vol10, vol20, ret1, ret5, ret20 = vals[i]
        
        # 冷却期：上次交易>15个交易日后才能再交易
        last_date = last_trade_date.get(code)
        if last_date is not None:
            days_since = (date - last_date).days
            if days_since < 15:
                continue
        
        # 大盘上升
        csi = csi_dict.get(date)
        if csi is None or csi[0] <= csi[1]:
            continue
        
        # 个股上升趋势
        if ma5 <= ma20 or ma20 <= 0 or pd.isna(ma20):
            continue
        
        # 前期涨幅>5%
        if pd.isna(ret20) or ret20 <= 0.05:
            continue
        
        # 缩量回调：成交量<5日均量85%
        if vol >= vol5 * 0.85 or vol5 <= 0:
            continue
        
        # 次日放量确认：涨幅>0.5% 且 成交量>5日均量1.2倍
        n_date, n_close, n_vol, n_ret1, n_vol5 = vals[i+1][0], vals[i+1][1], vals[i+1][2], vals[i+1][9], vals[i+1][5]
        if pd.isna(n_ret1) or n_ret1 <= 0.005 or pd.isna(n_vol5) or n_vol5 <= 0 or n_vol <= n_vol5 * 1.2:
            continue
        
        # 买入
        entry_price = float(n_close)
        entry_date = n_date
        stop_loss = entry_price * 0.97
        
        post_vals = vals[i+2:]
        exit_dt = None
        exit_px = None
        exit_rs = None
        max_ret = 0.0
        
        for f_idx, f_row in enumerate(post_vals):
            f_date, f_close = f_row[0], f_row[1]
            f_ma5, f_ma10 = f_row[3], f_row[4]
            days = f_idx + 1
            ret = (float(f_close) - entry_price) / entry_price
            
            if ret > max_ret:
                max_ret = ret
            
            # 止损3%
            if float(f_close) < stop_loss:
                exit_dt = f_date
                exit_px = float(f_close)
                exit_rs = 'stop_3pct'
                break
            
            # 止盈 MA10死叉
            if not (pd.isna(f_ma5) or pd.isna(f_ma10) or f_ma10 == 0):
                if float(f_ma5) < float(f_ma10):
                    exit_dt = f_date
                    exit_px = float(f_close)
                    exit_rs = 'profit_ma10_cross'
                    break
            
            # 持有7日
            if days >= 7:
                exit_dt = f_date
                exit_px = float(f_close)
                exit_rs = 'expire_7d'
                break
        
        if exit_dt and exit_px and entry_price > 0:
            last_trade_date[code] = exit_dt
            final_ret = (exit_px - entry_price) / entry_price
            trades.append({
                'code': code,
                'sig_date': str(pd.Timestamp(entry_date).date()),
                'entry_date': str(pd.Timestamp(entry_date).date()),
                'exit_date': str(pd.Timestamp(exit_dt).date()),
                'return': final_ret,
                'exit_reason': exit_rs,
                'hold_days': (pd.Timestamp(exit_dt) - pd.Timestamp(entry_date)).days,
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

trades_df['csi_return'] = trades_df.apply(lambda r: get_csi(r['entry_date'], r['exit_date']), axis=1)
trades_df['excess_return'] = trades_df['return'] - trades_df['csi_return']

rets = trades_df['return'].values
excess = trades_df['excess_return'].dropna().values
win = float((rets > 0).mean())
avg = float(rets.mean())
avg_ex = float(excess.mean()) if len(excess) > 0 else 0

print("\n" + "=" * 50)
print("H-014 结果")
print("=" * 50)
print("交易数: %d" % len(trades))
print("胜率: %.1f%%" % (win * 100))
print("平均收益: %+.2f%%" % (avg * 100))
print("平均超额收益: %+.2f%%" % (avg_ex * 100))
print("最大盈利: %+.2f%%" % (rets.max() * 100))
print("最大亏损: %+.2f%%" % (rets.min() * 100))

sig = sig_test([{'return': float(r)} for r in rets], name='H-014')
print("显著性: %s" % sig.get('conclusion', '?'))

print("\n出场:")
for reason, cnt in trades_df['exit_reason'].value_counts().items():
    print("  %s: %d (%.1f%%)" % (reason, cnt, cnt/len(trades)*100))

wins = rets[rets > 0]
losses = rets[rets < 0]
if len(wins) > 0 and len(losses) > 0:
    print("盈亏比: %.2f" % (wins.mean() / abs(losses.mean())))
print("持有天数: mean=%.1f" % trades_df['hold_days'].mean())

trades_df.to_csv(OUT + '/H014_trades.csv', index=False)
print("DONE")