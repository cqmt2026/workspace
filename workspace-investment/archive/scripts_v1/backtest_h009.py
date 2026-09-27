"""
H-009 关键点突破买入 回测
利弗莫尔关键点 + 趋势确认 + 缩量回踩买入
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
print("H-009 回测 - 关键点突破买入")
print("=" * 60)

# 加载样本
codes = open(CODES_FILE).read().strip().split('\n')
print("样本: %d只" % len(codes))

# 加载CSI300
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

# 加载样本股
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

# 计算指标
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
    g['ret1'] = g['close'].pct_change(1)
    g['ret5'] = g['close'].pct_change(5)
    g['ret20'] = g['close'].pct_change(20)
    # 前期高点（前20日最高收盘价 = 关键点）
    g['key_high'] = g['close'].rolling(20).max()
    # 从低点的反弹幅度
    g['low20'] = g['close'].rolling(20).min()
    g['pullback_pct'] = (g['close'] - g['low20']) / g['low20']  # 回踩幅度
    rows.append(g)
df = pd.concat(rows, ignore_index=True)
df = df[df['date'] >= '2019-06-01'].copy()
print("有效数据: %d行" % len(df))

# 信号日：每周1个
all_dates = sorted(df['date'].unique())
sig_dates = all_dates[::5]
print("信号日: %d个" % len(sig_dates))

trades = []

for sig_date in sig_dates:
    # 条件F：大盘MA5>MA20（上升趋势）
    csi_info = csi_dict.get(sig_date, None)
    if csi_info is None or csi_info['ma5'] <= csi_info['ma20']:
        continue
    
    day_df = df[df['date'] == sig_date].copy()
    if len(day_df) == 0:
        continue
    
    day_df = day_df[
        day_df['close'] > 0 &
        day_df['vol5'].notna() & (day_df['vol5'] > 0) &
        day_df['vol20'].notna() & (day_df['vol20'] > 0) &
        day_df['key_high'].notna() &
        day_df['pullback_pct'].notna()
    ]
    
    # === 核心条件：回踩关键点后放量突破 ===
    
    # 条件1: 回踩幅度5-20%（充分回调但不破前低）
    cond1 = (day_df['pullback_pct'] >= 0.05) & (day_df['pullback_pct'] <= 0.20)
    
    # 条件2: 股价接近前期高点（回踩到关键点附近）
    cond2 = day_df['close'] >= day_df['key_high'] * 0.85  # 回到85%以上区域
    
    # 条件3: 缩量（卖方减少，主力控盘）
    cond3 = day_df['volume'] < day_df['vol5'] * 0.80  # 缩量80%以下
    
    # 条件4: 当日放量上涨（突破确认）
    cond4 = (day_df['ret1'] > 0) & (day_df['volume'] > day_df['vol20'] * 1.3)
    
    # 条件5: 收盘站稳当日高点（确认突破）
    cond5 = day_df['close'] >= day_df['key_high'] * 0.97
    
    candidates = day_df[cond1 & cond2 & cond3 & cond4 & cond5].copy()
    
    if len(candidates) == 0:
        continue
    
    # 选当日涨幅最大的2只（突破最明确的）
    top2 = candidates.nlargest(2, 'ret1')
    
    for _, row in top2.iterrows():
        code = row['code']
        entry_price = float(row['close'])
        key_level = float(row['key_high'])
        stop_loss = entry_price * 0.97  # 跌破关键点3%止损
        
        stock_post = df[(df['code'] == code) & (df['date'] > sig_date)].sort_values('date')
        
        entry_date = sig_date
        exit_date = None
        exit_price = None
        exit_reason = None
        max_return = 0.0
        risk = entry_price - stop_loss
        
        for i, (idx, future_row) in enumerate(stock_post.iterrows()):
            days = i + 1
            price = float(future_row['close'])
            ret = (price - entry_price) / entry_price
            vol5_val = float(future_row['vol5']) if not pd.isna(future_row['vol5']) else None
            vol20_val = float(future_row['vol20']) if not pd.isna(future_row['vol20']) else None
            ma5_val = float(future_row['ma5']) if not pd.isna(future_row['ma5']) else None
            ma10_val = float(future_row['ma10']) if not pd.isna(future_row['ma10']) else None
            
            if ret > max_return:
                max_return = ret
            
            # 止损1：跌破关键点（-3%）
            if price < stop_loss:
                exit_date = future_row['date']
                exit_price = price
                exit_reason = 'stop_key_break'
                break
            
            # 止盈1：达到风险2倍
            if ret >= 0.06 and risk > 0:  # 风险2倍(3%*2=6%)
                # MA5跌破止盈
                if ma5_val and price < ma5_val:
                    exit_date = future_row['date']
                    exit_price = price
                    exit_reason = 'profit_2r'
                    break
            
            # 止盈2：高位放量大阴线
            if vol5_val and vol20_val and vol5_val > vol20_val * 2:
                if price < float(future_row['open']):
                    exit_date = future_row['date']
                    exit_price = price
                    exit_reason = 'profit_volume'
                    break
            
            # 止盈3：跌破MA5（趋势结束）
            if ma5_val and ma5_val > 0 and price < ma5_val:
                exit_date = future_row['date']
                exit_price = price
                exit_reason = 'trend_end'
                break
            
            # 10日到期
            if days >= 10:
                exit_date = future_row['date']
                exit_price = price
                exit_reason = 'expire_10d'
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
                'key_level': key_level,
                'stop_loss': stop_loss,
                'return': final_ret,
                'exit_reason': exit_reason,
                'hold_days': (exit_date - entry_date).days,
                'max_return': max_return,
                'pullback_pct': float(row['pullback_pct'])
            })

print("\n交易结果: %d笔" % len(trades))

if len(trades) == 0:
    print("无交易信号")
    sys.exit(0)

trades_df = pd.DataFrame(trades)

# CSI300对比
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
print("H-009 回测结果")
print("=" * 50)
print("交易数: %d" % len(trades))
print("胜率: %.1f%%" % (win_rate * 100))
print("平均收益: %+.2f%%" % (avg_ret * 100))
print("平均超额收益: %+.2f%%" % (avg_excess * 100))
print("最大盈利: %+.2f%%" % (rets.max() * 100))
print("最大亏损: %+.2f%%" % (rets.min() * 100))
print("收益标准差: %.2f%%" % (rets.std() * 100))

sig = sig_test([{'return': float(r)} for r in rets], name='H-009')
print("显著性: %s (%s)" % (sig.get('conclusion', '?'), sig.get('conclusion_detail', '')))

print("\n出场原因:")
for reason, cnt in trades_df['exit_reason'].value_counts().items():
    print("  %s: %d (%.1f%%)" % (reason, cnt, cnt/len(trades)*100))

print("\n持有天数: mean=%.1f" % trades_df['hold_days'].mean())

# 保存
trades_df.to_csv(OUT + '/H009_trades.csv', index=False)
print("\n已保存: " + OUT + '/H009_trades.csv')
print("DONE")