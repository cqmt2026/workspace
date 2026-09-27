"""
H-011 趋势确认+口袋支点 回测
结合H-008稳健性 + H-010高弹性
改进点：
1. 先确认趋势（MA10>MA20均线多头）
2. 回踩到MA10/MA20支撑位时买入
3. 更严格的止损（昨日低点下方1%）
4. 固定持有5日（避免被洗出）
5. RSI辅助判断超买超卖
样本：500只优质股票
"""

import sqlite3
import pandas as pd
import numpy as np
import json
import os
import sys

DB = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\market_data.db'
CODES_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ta_backtest\sample_500.txt'
OUT = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ta_backtest'
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts')
from significance_test import run as sig_test

print("=" * 60)
print("H-011 回测 - 趋势确认+口袋支点")
print("=" * 60)

codes = open(CODES_FILE).read().strip().split('\n')
print("样本: %d只" % len(codes))

conn = sqlite3.connect(DB)
csi300 = pd.read_sql(
    "SELECT date, close FROM daily_k WHERE code='sh.000300' AND date>='2019-01-01' ORDER BY date",
    conn
)
csi300['date'] = pd.to_datetime(csi300['date'])
csi300 = csi300.sort_values('date').reset_index(drop=True)
csi300['ma5'] = csi300['close'].rolling(5).mean()
csi300['ma20'] = csi300['close'].rolling(20).mean()
csi_dict = csi300.set_index('date')[['ma5', 'ma20']].to_dict('index')
print("CSI300: %d天" % len(csi300))
conn.close()

cs = ','.join(["'" + c + "'" for c in codes])
conn = sqlite3.connect(DB)
df = pd.read_sql(
    "SELECT code, date, open, high, low, close, volume FROM daily_k "
    "WHERE code IN (%s) AND date>='2019-01-01' ORDER BY code, date" % cs, conn
)
conn.close()
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date']).reset_index(drop=True)
print("数据: %d行" % len(df))

print("计算指标...")
rows = []
for code, grp in df.groupby('code'):
    g = grp.sort_values('date').copy()
    g['ma5'] = g['close'].rolling(5).mean()
    g['ma10'] = g['close'].rolling(10).mean()
    g['ma20'] = g['close'].rolling(20).mean()
    g['vol5'] = g['volume'].rolling(5).mean()
    g['vol10'] = g['volume'].rolling(10).mean()
    g['vol20'] = g['volume'].rolling(20).mean()
    g['vol20_std'] = g['volume'].rolling(20).std()
    g['ret1'] = g['close'].pct_change(1)
    g['ret5'] = g['close'].pct_change(5)
    g['ret20'] = g['close'].pct_change(20)
    g['high20'] = g['high'].rolling(20).max()
    g['low20'] = g['low'].rolling(20).min()
    g['range20'] = (g['high20'] - g['low20']) / g['low20']
    # RSI(14)
    delta = g['close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, 0.001)
    g['rsi14'] = 100 - (100 / (1 + rs))
    # 昨日收盘（用于止损）
    g['prev_close'] = g['close'].shift(1)
    g['prev_low'] = g['low'].shift(1)
    rows.append(g)
df = pd.concat(rows, ignore_index=True)
df = df[df['date'] >= '2019-06-01'].copy()
print("有效数据: %d行" % len(df))

all_dates = sorted(df['date'].unique())
sig_dates = all_dates[::5]
print("信号日: %d个" % len(sig_dates))

trades = []

for sig_date in sig_dates:
    # 条件F：大盘MA5>MA20
    csi_info = csi_dict.get(sig_date, None)
    if csi_info is None or csi_info['ma5'] <= csi_info['ma20']:
        continue
    
    day_df = df[df['date'] == sig_date].copy()
    if len(day_df) == 0:
        continue
    
    day_df = day_df[
        day_df['close'] > 0 &
        day_df['ma5'].notna() & day_df['ma10'].notna() & day_df['ma20'].notna() &
        day_df['vol5'].notna() & (day_df['vol5'] > 0) &
        day_df['vol20'].notna() & (day_df['vol20'] > 0) &
        day_df['rsi14'].notna() &
        day_df['prev_low'].notna()
    ]
    
    # === 核心条件 ===
    
    # 条件1：趋势确认（MA10>MA20均线多头）
    cond1 = (day_df['ma10'] > day_df['ma20']) & (day_df['ma5'] > day_df['ma10'])
    
    # 条件2：回踩均线（股价在MA5-MA10之间，且接近MA10）
    # 价格在MA5和MA10之间，且MA5距MA10不超过5%
    cond2 = (day_df['close'] < day_df['ma5']) & (day_df['close'] >= day_df['ma10']) & \
            (day_df['ma5'] - day_df['close']) < day_df['ma5'] * 0.02
    
    # 条件3：RSI在40-65区间（不过热，不冷淡）
    cond3 = (day_df['rsi14'] >= 40) & (day_df['rsi14'] <= 65)
    
    # 条件4：缩量（卖方衰竭）
    cond4 = day_df['volume'] < day_df['vol5'] * 0.85
    
    # 条件5：当日放量中阳线（止跌信号）
    cond5 = (day_df['ret1'] > 0.01) & (day_df['ret1'] < 0.05) & \
            (day_df['volume'] > day_df['vol20'] * 1.2)
    
    candidates = day_df[cond1 & cond2 & cond3 & cond4 & cond5].copy()
    
    if len(candidates) == 0:
        continue
    
    # 选RSI最低的2只（回调最深、最有价值）
    top2 = candidates.nsmallest(2, 'rsi14')
    
    for _, row in top2.iterrows():
        code = row['code']
        entry_price = float(row['close'])
        stop_loss = min(float(row['prev_low']), entry_price * 0.97)  # 昨日低点 或 -3%
        
        stock_post = df[(df['code'] == code) & (df['date'] > sig_date)].sort_values('date')
        
        entry_date = sig_date
        exit_date = None
        exit_price = None
        exit_reason = None
        max_return = 0.0
        
        for i, (idx, future_row) in enumerate(stock_post.iterrows()):
            days = i + 1
            price = float(future_row['close'])
            ret = (price - entry_price) / entry_price
            ma5_val = float(future_row['ma5']) if not pd.isna(future_row['ma5']) else None
            ma10_val = float(future_row['ma10']) if not pd.isna(future_row['ma10']) else None
            rsi_val = float(future_row['rsi14']) if not pd.isna(future_row['rsi14']) else None
            
            if ret > max_return:
                max_return = ret
            
            # 止损：跌破昨日低点或-3%
            prev_low_val = float(future_row['prev_low']) if not pd.isna(future_row['prev_low']) else None
            if prev_low_val and price < prev_low_val:
                exit_date = future_row['date']
                exit_price = price
                exit_reason = 'stop_prev_low'
                break
            if price < stop_loss:
                exit_date = future_row['date']
                exit_price = price
                exit_reason = 'stop_3pct'
                break
            
            # 止盈1：RSI>75超买
            if rsi_val and rsi_val > 75:
                exit_date = future_row['date']
                exit_price = price
                exit_reason = 'profit_rsi_overbought'
                break
            
            # 止盈2：MA5下穿MA10
            if ma5_val and ma10_val and ma5_val < ma10_val:
                exit_date = future_row['date']
                exit_price = price
                exit_reason = 'profit_ma5_cross'
                break
            
            # 止盈3：持有5日
            if days >= 5:
                exit_date = future_row['date']
                exit_price = price
                exit_reason = 'expire_5d'
                break
        
        if exit_date and exit_price and entry_price > 0:
            final_ret = (exit_price - entry_price) / entry_price
            trades.append({
                'code': code,
                'sig_date': str(sig_date.date()),
                'entry_date': str(entry_date.date()),
                'exit_date': str(exit_date.date()),
                'entry_price': entry_price,
                'exit_price': exit_price,
                'stop_loss': stop_loss,
                'return': final_ret,
                'exit_reason': exit_reason,
                'hold_days': (exit_date - entry_date).days,
                'max_return': max_return,
                'rsi14': float(row['rsi14']),
                'pullback_pct': (float(row['ma10']) - entry_price) / float(row['ma10']) if float(row['ma10']) > 0 else 0
            })

print("\n交易结果: %d笔" % len(trades))

if len(trades) == 0:
    print("无交易信号")
    sys.exit(0)

trades_df = pd.DataFrame(trades)

def get_csi_return(start_date, end_date):
    d1 = csi300[csi300['date'] == pd.Timestamp(start_date)]
    d2 = csi300[csi300['date'] == pd.Timestamp(end_date)]
    if len(d1) == 0 or len(d2) == 0:
        return None
    return (float(d2['close'].values[0]) - float(d1['close'].values[0])) / float(d1['close'].values[0])

trades_df['csi_return'] = trades_df.apply(
    lambda r: get_csi_return(r['entry_date'], r['exit_date']), axis=1
)
trades_df['excess_return'] = trades_df['return'] - trades_df['csi_return']

rets = trades_df['return'].values
excess_rets = trades_df['excess_return'].dropna().values

win_rate = float((rets > 0).mean())
avg_ret = float(rets.mean())
avg_excess = float(excess_rets.mean()) if len(excess_rets) > 0 else 0

print("\n" + "=" * 50)
print("H-011 回测结果")
print("=" * 50)
print("交易数: %d" % len(trades))
print("胜率: %.1f%%" % (win_rate * 100))
print("平均收益: %+.2f%%" % (avg_ret * 100))
print("平均超额收益: %+.2f%%" % (avg_excess * 100))
print("最大盈利: %+.2f%%" % (rets.max() * 100))
print("最大亏损: %+.2f%%" % (rets.min() * 100))
print("收益标准差: %.2f%%" % (rets.std() * 100))

sig = sig_test([{'return': float(r)} for r in rets], name='H-011')
print("显著性: %s (%s)" % (sig.get('conclusion', '?'), sig.get('conclusion_detail', '')))

print("\n出场原因:")
for reason, cnt in trades_df['exit_reason'].value_counts().items():
    print("  %s: %d (%.1f%%)" % (reason, cnt, cnt/len(trades)*100))

print("\n持有天数: mean=%.1f" % trades_df['hold_days'].mean())

# 盈亏比
wins = rets[rets > 0]
losses = rets[rets < 0]
if len(wins) > 0 and len(losses) > 0:
    print("盈亏比: %.2f" % (wins.mean() / abs(losses.mean())))

trades_df.to_csv(OUT + '/H011_trades.csv', index=False)
print("\n已保存: " + OUT + '/H011_trades.csv')
print("DONE")