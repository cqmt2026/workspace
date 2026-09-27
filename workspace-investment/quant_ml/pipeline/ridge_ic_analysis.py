import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t0 = time.time()
print('Ridge IC分析 - 线性模型环节', flush=True)
print('='*60, flush=True)

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from scipy.stats import spearmanr
import sqlite3

print(f'导入完成 ({time.time()-t0:.1f}s)', flush=True)

conn = sqlite3.connect('F:/market_data.db')
df = pd.read_sql('SELECT code, date, close, volume FROM daily_k WHERE date >= "2025-01-01" ORDER BY code, date', conn)
conn.close()
df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
print(f'数据: {len(df)}行, {df["code"].nunique()}只股票 ({time.time()-t0:.1f}s)', flush=True)

BASIC_FACTORS = {
    'ret_1d': lambda c,v,i: c[i]/c[i-1]-1,
    'ret_5d': lambda c,v,i: c[i]/c[i-5]-1,
    'ret_20d': lambda c,v,i: c[i]/c[i-20]-1,
    'vol_20d': lambda c,v,i: np.std(c[i-20:i+1])/np.mean(c[i-20:i+1]) if np.mean(c[i-20:i+1])>0 else 0,
    'ma5_ratio': lambda c,v,i: c[i]/np.mean(c[i-5:i+1]),
    'ma20_ratio': lambda c,v,i: c[i]/np.mean(c[i-20:i+1]),
    'volume_ratio': lambda c,v,i: v[i]/np.mean(v[i-5:i+1]) if np.mean(v[i-5:i+1])>0 else 1,
}

all_records = []
codes = df['code'].unique()
print(f'计算因子 ({len(codes)}只股票)...', flush=True)
for idx, code in enumerate(codes):
    if idx % 1000 == 0: print(f'  {idx}/{len(codes)}', flush=True)
    sub = df[df['code']==code].copy().sort_values('date').reset_index(drop=True)
    if len(sub) < 120: continue
    c = sub['close'].values.astype(np.float64)
    v = sub['volume'].values.astype(np.float64)
    for i in range(60, len(sub)-10):
        row = {'date':sub['date'].iloc[i], 'code':code}
        for fn, ff in BASIC_FACTORS.items(): row[fn] = ff(c,v,i)
        row['fwd_ret'] = c[i+10]/c[i]-1
        all_records.append(row)

factor_df = pd.DataFrame(all_records)
print(f'有效样本: {len(factor_df)} ({time.time()-t0:.1f}s)', flush=True)

factor_names = list(BASIC_FACTORS.keys())
dates = sorted(factor_df['date'].unique())
window_size = 60
ic_records = []

print('滚动IC分析...', flush=True)
for i in range(window_size, len(dates)):
    train_end = dates[i]
    train_start = dates[i-window_size]
    train = factor_df[(factor_df['date']>=train_start)&(factor_df['date']<train_end)]
    test = factor_df[factor_df['date']==train_end]
    if len(train)<100 or len(test)<10: continue
    model = Ridge(alpha=1.0)
    model.fit(train[factor_names].values, train['fwd_ret'].values)
    y_pred = model.predict(test[factor_names].values)
    y_test = test['fwd_ret'].values
    pic = np.corrcoef(y_pred, y_test)[0,1] if np.std(y_pred)>0 and np.std(y_test)>0 else 0
    ric, _ = spearmanr(y_pred, y_test)
    ic_records.append({'date':train_end, 'pearson_ic':pic, 'rank_ic':ric, 'n':len(test)})

ic_df = pd.DataFrame(ic_records)
print(f'\n{"="*60}', flush=True)
print(f'IC分析结果 ({len(ic_df)}个窗口)', flush=True)
if len(ic_df) > 0:
    print(f'Pearson IC: 均值={ic_df["pearson_ic"].mean():.4f} 标准差={ic_df["pearson_ic"].std():.4f} ICIR={ic_df["pearson_ic"].mean()/ic_df["pearson_ic"].std():.4f}', flush=True)
    print(f'Rank IC:    均值={ic_df["rank_ic"].mean():.4f} 标准差={ic_df["rank_ic"].std():.4f} ICIR={ic_df["rank_ic"].mean()/ic_df["rank_ic"].std():.4f}', flush=True)
    print(f'IC>0比例: {(ic_df["pearson_ic"]>0).mean()*100:.1f}%', flush=True)

model_all = Ridge(alpha=1.0)
model_all.fit(factor_df[factor_names].values, factor_df['fwd_ret'].values)
print(f'\n因子重要性:', flush=True)
for fn, coef in sorted(zip(factor_names, model_all.coef_), key=lambda x:abs(x[1]), reverse=True):
    print(f'  {fn:15s}  {coef:+.6f}', flush=True)

print(f'\n总耗时: {time.time()-t0:.1f}s', flush=True)