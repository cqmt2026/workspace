import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t0 = time.time()
print('分层收益分析', flush=True)
print('='*60, flush=True)

import numpy as np
import pandas as pd
import lightgbm as lgb
import sqlite3

print(f'导入 {time.time()-t0:.1f}s', flush=True)

conn = sqlite3.connect('F:/market_data.db')
print('查询DB...', flush=True)
df = pd.read_sql(
    'SELECT code, date, close, volume, high, low FROM daily_k WHERE date >= "2023-01-01" ORDER BY code, date LIMIT 500000',
    conn)
conn.close()
df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
print(f'数据 {len(df)}行 {df["code"].nunique()}只 ({time.time()-t0:.1f}s)', flush=True)

# 取前200只股票
codes = df['code'].unique()[:200]
records = []
print(f'计算特征 {len(codes)}只...', flush=True)
for idx, code in enumerate(codes):
    if idx % 50 == 0: print(f'  {idx}/{len(codes)}', flush=True)
    sub = df[df['code']==code].sort_values('date').reset_index(drop=True)
    if len(sub) < 60: continue
    c = sub['close'].values.astype(float)
    v = sub['volume'].values.astype(float)
    h = sub['high'].values.astype(float)
    l = sub['low'].values.astype(float)
    for i in range(60, len(sub)-10):
        fwd = c[i+10]/c[i]-1
        records.append({
            'ret_1': c[i]/c[i-1]-1, 'ret_5': c[i]/c[i-5]-1, 'ret_10': c[i]/c[i-10]-1,
            'ma5_r': c[i]/np.mean(c[i-5:i+1]), 'ma20_r': c[i]/np.mean(c[i-20:i+1]),
            'vol_20': np.std(c[i-20:i+1])/np.mean(c[i-20:i+1]),
            'v_ratio5': v[i]/np.mean(v[i-5:i+1]) if np.mean(v[i-5:i+1])>0 else 1,
            'pos20': (c[i]-np.min(l[i-20:i+1]))/(np.max(h[i-20:i+1])-np.min(l[i-20:i+1])+1e-9),
            'fwd_ret': fwd, 'label': 1 if fwd > 0 else 0,
        })

data = pd.DataFrame(records)
print(f'样本 {len(data)} ({time.time()-t0:.1f}s)', flush=True)
if len(data) < 1000: print('样本不足, 退出', flush=True); exit()

split = int(len(data)*0.7)
train, test = data[:split], data[split:]
feat = ['ret_1','ret_5','ret_10','ma5_r','ma20_r','vol_20','v_ratio5','pos20']
print(f'训练 {len(train)} 测试 {len(test)}', flush=True)

model = lgb.LGBMClassifier(
    n_estimators=200, learning_rate=0.03, num_leaves=24, max_depth=5,
    feature_fraction=0.7, reg_alpha=0.05, reg_lambda=0.1, is_unbalance=True,
    verbose=-1, random_state=42, n_jobs=-1)
model.fit(train[feat], train['label'],
          eval_set=[(train[feat], train['label'])],
          eval_metric='auc', callbacks=[lgb.early_stopping(15), lgb.log_evaluation(0)])

y_prob = model.predict_proba(test[feat])[:,1]
test = test.copy()
test['prob'] = y_prob
test['layer'] = pd.qcut(test['prob'], 10, labels=False, duplicates='drop')

print(f'\n{"="*60}', flush=True)
print(f'分层收益 (测试集)', flush=True)
print(f'{"层":>4s} | {"样本":>6s} | {"收益":>8s} | {"胜率":>6s}', flush=True)
print('-'*60, flush=True)
for l in range(test['layer'].nunique()):
    s = test[test['layer']==l]
    print(f'{l:4d} | {len(s):6d} | {s["fwd_ret"].mean():+.4f} | {(s["fwd_ret"]>0).mean():.0%}', flush=True)

t = test[test['layer']==test['layer'].max()]['fwd_ret']
b = test[test['layer']==test['layer'].min()]['fwd_ret']
print(f'\nTop层: {t.mean():+.4f} ({len(t)}样本)', flush=True)
print(f'Bottom层: {b.mean():+.4f} ({len(b)}样本)', flush=True)
print(f'多空差: {t.mean()-b.mean():+.4f}', flush=True)

print(f'\n总耗时: {time.time()-t0:.1f}s', flush=True)