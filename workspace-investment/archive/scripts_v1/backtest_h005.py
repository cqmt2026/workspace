"""
H-005 均值回归买点 回测
样本：500只优质股票（2019-2026完整数据）
对比：沪深300基准
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
print("H-005 回测 - 500只样本")
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
csi300['ret5'] = csi300['close'].pct_change(5)
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
    g['ret5'] = g['close'].pct_change(5)
    g['ret20'] = g['close'].pct_change(20)
    g['vol5'] = g['volume'].rolling(5).mean()
    g['ret1'] = g['close'].pct_change(1)
    # 前20日最大涨幅（用于选强势股）
    g['high20'] = g['close'].rolling(20).max()
    g['ret20_from_low'] = (g['close'] - g['close'].rolling(20).min()) / g['close'].rolling(20).min()
    rows.append(g)
df = pd.concat(rows, ignore_index=True)
df = df[df['date'] >= '2019-06-01'].copy()
print("有效数据: %d行" % len(df))

# 信号日（每月1个）
all_dates = sorted(df['date'].unique())
# 选择每月10号作为信号日（避开月初效应）
sig_dates = [d for d in all_dates if d.day >= 10][::20]
print("信号日: %d个" % len(sig_dates))

# 预先计算每只股票的20日涨幅排名
def rank_by_ret20(group, date):
    """某日某股票的20日涨幅在当日全市场中的排名百分比"""
    day_df = df[df['date'] == date].copy()
    day_df = day_df[day_df['ret20'].notna() & (day_df['close'] > 0)]
    if len(day_df) == 0:
        return 0
    pct = (day_df['ret20'] >= group[group['date']==date]['ret20'].values[0]).mean()
    return pct

# CSI300 MA5>MA20 的日期
csi_dict = csi300.set_index('date')[['ma5', 'ma20']].to_dict('index')

trades = []
stop_trades = []

for sig_date in sig_dates:
    # F条件：大盘MA5>MA20
    csi_info = csi_dict.get(sig_date, None)
    if csi_info is None or csi_info['ma5'] <= csi_info['ma20']:
        continue
    
    day_df = df[df['date'] == sig_date].copy()
    if len(day_df) == 0:
        continue
    
    # 计算每只股票的ret20排名（强势股）
    day_df = day_df[day_df['ret20'].notna() & (day_df['ma5'].notna()) & day_df['vol5'].notna() & (day_df['vol5'] > 0)]
    
    # A. 强势股：ret20前20%
    threshold_A = day_df['ret20'].quantile(0.80)
    
    # 满足条件的股票
    cond_A = day_df['ret20'] >= threshold_A
    cond_B = day_df['ret5'] < 0  # 短期回调
    cond_C = day_df['ma5'] > day_df['ma10']  # MA5仍向上
    cond_D = day_df['volume'] < day_df['vol5'] * 0.7  # 缩量
    cond_E = day_df['close'] >= (day_df['high'] + day_df['low']) / 2  # 收盘站稳
    
    candidates = day_df[cond_A & cond_B & cond_C & cond_D & cond_E].copy()
    
    if len(candidates) == 0:
        continue
    
    # 选ret20最高的3只（最强势的回调股）
    top3 = candidates.nlargest(3, 'ret20')
    
    for _, row in top3.iterrows():
        code = row['code']
        entry_price = float(row['close'])
        
        # 获取后续N日数据（最多20日）
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
            
            if ret > max_return:
                max_return = ret
            
            # 止损
            if ret <= -0.03:
                exit_date = future_row['date']
                exit_price = price
                exit_reason = 'stop_loss'
                break
            
            # 止盈（MA5止损）
            if days >= 5 and ret >= 0.05:
                if ma5_val and price < ma5_val:
                    exit_date = future_row['date']
                    exit_price = price
                    exit_reason = 'profit_stop_5d'
                    break
            if days >= 10 and ret >= 0.08:
                if ma5_val and price < ma5_val:
                    exit_date = future_row['date']
                    exit_price = price
                    exit_reason = 'profit_stop_10d'
                    break
            
            # 20日到期
            if days >= 20:
                exit_date = future_row['date']
                exit_price = price
                exit_reason = 'expire_20d'
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
                'return': final_ret,
                'exit_reason': exit_reason,
                'hold_days': (exit_date - entry_date).days,
                'max_return': max_return
            })

print("\n交易结果: %d笔" % len(trades))

if len(trades) == 0:
    print("无交易信号")
    sys.exit(0)

trades_df = pd.DataFrame(trades)

# 对比CSI300同期收益
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

# 分析
rets = trades_df['return'].values
excess_rets = trades_df['excess_return'].dropna().values

win_rate = float((rets > 0).mean())
avg_ret = float(rets.mean())
avg_excess = float(excess_rets.mean()) if len(excess_rets) > 0 else 0

print("\n--- H-005 回测结果 ---")
print("交易数: %d" % len(trades))
print("胜率: %.1f%%" % (win_rate * 100))
print("平均收益: %+.2f%%" % (avg_ret * 100))
print("平均超额收益: %+.2f%%" % (avg_excess * 100))

sig = sig_test([{'return': float(r)} for r in rets], name='H-005')
print("显著性: %s (%s)" % (sig.get('conclusion', '?'), sig.get('conclusion_detail', '')))

print("\n--- 各维度统计 ---")
print("持有天数分布: mean=%.1f" % trades_df['hold_days'].mean())
exit_reasons = trades_df['exit_reason'].value_counts()
print("出场原因:")
for reason, cnt in exit_reasons.items():
    print("  %s: %d" % (reason, cnt))

print("\n--- 盈亏分布 ---")
print("盈利: %d (%.1f%%)" % ((rets > 0).sum(), (rets > 0).mean() * 100))
print("亏损: %d (%.1f%%)" % ((rets < 0).sum(), (rets < 0).mean() * 100))
print("最大单笔盈利: %+.2f%%" % (rets.max() * 100))
print("最大单笔亏损: %+.2f%%" % (rets.min() * 100))
print("收益标准差: %.2f%%" % (rets.std() * 100))

# 保存
trades_df.to_csv(OUT + '/H005_trades.csv', index=False)
print("\n已保存: " + OUT + '/H005_trades.csv')