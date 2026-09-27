"""
H-012 低位首板涨停回调买入 - 超简版
用SQL预计算所有指标，直接在DB里做筛选
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
print("H-012 - 低位首板涨停回调买入")
print("=" * 60)

codes = open(CODES_FILE).read().strip().split('\n')
print("样本: %d只" % len(codes))

conn = sqlite3.connect(DB)

# CSI300
csi300 = pd.read_sql(
    "SELECT date, close FROM daily_k WHERE code='sh.000300' AND date>='2019-01-01' ORDER BY date",
    conn
)
csi300['date'] = pd.to_datetime(csi300['date'])
csi300 = csi300.sort_values('date').reset_index(drop=True)
csi300['ma5'] = csi300['close'].rolling(5).mean()
csi300['ma20'] = csi300['close'].rolling(20).mean()
csi_dict = csi300.set_index('date')[['ma5', 'ma20']].to_dict('index')

cs = ','.join(["'" + c + "'" for c in codes])
df = pd.read_sql(
    "SELECT code, date, open, high, low, close, volume FROM daily_k "
    "WHERE code IN (%s) AND date>='2019-01-01' ORDER BY code, date" % cs, conn
)
conn.close()
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date']).reset_index(drop=True)

# 用SQL窗口函数一次性计算所有需要的指标
print("计算指标...")
df['prev_close'] = df.groupby('code')['close'].shift(1)
df['prev_low'] = df.groupby('code')['low'].shift(1)
df['ma5'] = df.groupby('code')['close'].transform(lambda x: x.rolling(5).mean())
df['ma10'] = df.groupby('code')['close'].transform(lambda x: x.rolling(10).mean())
df['vol5'] = df.groupby('code')['volume'].transform(lambda x: x.rolling(5).mean())
df['vol20'] = df.groupby('code')['volume'].transform(lambda x: x.rolling(20).mean())
df['ret1'] = df.groupby('code')['close'].pct_change(1)

# 标记涨停日（当日/前日涨停）
df['limit_up'] = (df['close'] / df['prev_close'] >= 1.095) & df['prev_close'].notna() & (df['prev_close'] > 0)

# 识别低位涨停（涨停前30日涨幅<50%）
print("识别低位涨停...")
lu_records = {}
for code, grp in df.groupby('code'):
    g = grp.sort_values('date').copy()
    for i in range(30, len(g)):
        if g.iloc[i]['limit_up']:
            p30 = float(g.iloc[i-30]['close']) if i >= 30 else float(g.iloc[0]['close'])
            pc = float(g.iloc[i]['prev_close'])
            if p30 > 0 and pc > 0 and (pc - p30) / p30 < 0.50:
                if code not in lu_records:
                    lu_records[code] = []
                lu_records[code].append({
                    'date': g.iloc[i]['date'],
                    'price': float(g.iloc[i]['close'])
                })

print("低位涨停: %d只股票，共%d次" % (len(lu_records), sum(len(v) for v in lu_records.values())))

# 构建候选买入日（涨停后1-10日内放量上涨）
print("生成候选买入日...")
candidates = []

for code, records in lu_records.items():
    stock = df[df['code'] == code].sort_values('date')
    for rec in records:
        lu_date = rec['date']
        lu_price = rec['price']
        
        # 涨停后1-10日
        post = stock[(stock['date'] > lu_date)].head(10)
        for i in range(1, len(post)):
            row = post.iloc[i]
            buy_date = row['date']
            
            vol5_val = float(row['vol5']) if not pd.isna(row['vol5']) and row['vol5'] > 0 else None
            ret1_val = float(row['ret1']) if not pd.isna(row['ret1']) else None
            vol = float(row['volume'])
            
            if vol5_val is None or ret1_val is None:
                continue
            
            # 放量上涨
            if ret1_val <= 0 or vol <= vol5_val * 1.5:
                continue
            
            # 大盘条件
            csi_info = csi_dict.get(buy_date, None)
            if csi_info is None or csi_info['ma5'] <= csi_info['ma20']:
                continue
            
            # 回调幅度5-25%
            post_buy = stock[(stock['date'] > lu_date) & (stock['date'] <= buy_date)]
            if len(post_buy) == 0:
                continue
            recent_low = float(post_buy['low'].min())
            pullback = (lu_price - recent_low) / lu_price
            if pullback < 0.05 or pullback > 0.25:
                continue
            
            candidates.append({
                'code': code,
                'buy_date': buy_date,
                'entry_price': float(row['close']),
                'stop_loss': min(float(row['prev_low']) if not pd.isna(row['prev_low']) else float(row['close']) * 0.97,
                                 float(row['close']) * 0.97),
                'vol_ratio': vol / vol5_val,
                'pullback': pullback,
                'ma5_val': float(row['ma5']) if not pd.isna(row['ma5']) else None,
                'ma10_val': float(row['ma10']) if not pd.isna(row['ma10']) else None
            })

print("候选买入日: %d个" % len(candidates))

if len(candidates) == 0:
    print("无候选")
    sys.exit(0)

# 执行回测
print("执行回测...")
trades = []

for cand in candidates:
    code = cand['code']
    buy_date = cand['buy_date']
    entry_price = cand['entry_price']
    stop_loss = cand['stop_loss']
    ma5_init = cand['ma5_val']
    ma10_init = cand['ma10_val']
    
    stock_post = df[(df['code'] == code) & (df['date'] > buy_date)].sort_values('date')
    if len(stock_post) == 0:
        continue
    
    exit_date = None
    exit_price = None
    exit_reason = None
    max_return = 0.0
    
    for i, (idx, row) in enumerate(stock_post.iterrows()):
        days = i + 1
        price = float(row['close'])
        ret = (price - entry_price) / entry_price
        ma5_f = float(row['ma5']) if not pd.isna(row['ma5']) else None
        ma10_f = float(row['ma10']) if not pd.isna(row['ma10']) else None
        prev_low_f = float(row['prev_low']) if not pd.isna(row['prev_low']) else None
        
        if ret > max_return:
            max_return = ret
        
        # 止损
        if prev_low_f and price < prev_low_f:
            exit_date = row['date']
            exit_price = price
            exit_reason = 'stop_prev_low'
            break
        if price < stop_loss:
            exit_date = row['date']
            exit_price = price
            exit_reason = 'stop_3pct'
            break
        
        # 止盈MA5死叉
        if ma5_f and ma10_f and ma5_f < ma10_f:
            exit_date = row['date']
            exit_price = price
            exit_reason = 'profit_ma5_cross'
            break
        
        # 10日到期
        if days >= 10:
            exit_date = row['date']
            exit_price = price
            exit_reason = 'expire_10d'
            break
    
    if exit_date and exit_price and entry_price > 0:
        final_ret = (exit_price - entry_price) / entry_price
        trades.append({
            'code': code,
            'sig_date': str(buy_date.date()),
            'entry_date': str(buy_date.date()),
            'exit_date': str(exit_date.date()),
            'entry_price': entry_price,
            'exit_price': exit_price,
            'return': final_ret,
            'exit_reason': exit_reason,
            'hold_days': (exit_date - buy_date).days,
            'max_return': max_return,
            'vol_ratio': cand['vol_ratio'],
            'pullback': cand['pullback']
        })

print("交易结果: %d笔" % len(trades))

if len(trades) == 0:
    print("无交易")
    sys.exit(0)

trades_df = pd.DataFrame(trades)

def get_csi_return(s, e):
    d1 = csi300[csi300['date'] == pd.Timestamp(s)]
    d2 = csi300[csi300['date'] == pd.Timestamp(e)]
    if len(d1) == 0 or len(d2) == 0:
        return None
    return (float(d2['close'].values[0]) - float(d1['close'].values[0])) / float(d1['close'].values[0])

trades_df['csi_return'] = trades_df.apply(lambda r: get_csi_return(r['entry_date'], r['exit_date']), axis=1)
trades_df['excess_return'] = trades_df['return'] - trades_df['csi_return']

rets = trades_df['return'].values
excess_rets = trades_df['excess_return'].dropna().values

win_rate = float((rets > 0).mean())
avg_ret = float(rets.mean())
avg_excess = float(excess_rets.mean()) if len(excess_rets) > 0 else 0

print("\n" + "=" * 50)
print("H-012 回测结果")
print("=" * 50)
print("交易数: %d" % len(trades))
print("胜率: %.1f%%" % (win_rate * 100))
print("平均收益: %+.2f%%" % (avg_ret * 100))
print("平均超额收益: %+.2f%%" % (avg_excess * 100))
print("最大盈利: %+.2f%%" % (rets.max() * 100))
print("最大亏损: %+.2f%%" % (rets.min() * 100))
print("收益标准差: %.2f%%" % (rets.std() * 100))

sig = sig_test([{'return': float(r)} for r in rets], name='H-012')
print("显著性: %s (%s)" % (sig.get('conclusion', '?'), sig.get('conclusion_detail', '')))

print("\n出场原因:")
for reason, cnt in trades_df['exit_reason'].value_counts().items():
    print("  %s: %d (%.1f%%)" % (reason, cnt, cnt/len(trades)*100))

print("\n持有天数: mean=%.1f" % trades_df['hold_days'].mean())

wins = rets[rets > 0]
losses = rets[rets < 0]
if len(wins) > 0 and len(losses) > 0:
    print("盈亏比: %.2f" % (wins.mean() / abs(losses.mean())))

trades_df.to_csv(OUT + '/H012_trades.csv', index=False)
print("\n已保存: " + OUT + '/H012_trades.csv')
print("DONE")