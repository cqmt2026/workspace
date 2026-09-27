import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t0 = time.time()
print('多模型对比', flush=True)
print('='*60, flush=True)

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import lightgbm as lgb
import sqlite3

print(f'导入 {time.time()-t0:.1f}s', flush=True)

conn = sqlite3.connect('F:/market_data.db')
print('查询DB...', flush=True)
df = pd.read_sql(
    'SELECT code, date, close, volume FROM daily_k WHERE date >= "2024-01-01" ORDER BY code, date LIMIT 300000',
    conn)
conn.close()
df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
print(f'数据 {len(df)}行 {df["code"].nunique()}只 ({time.time()-t0:.1f}s)', flush=True)

codes = df['code'].unique()[:200]
records = []
print(f'计算特征 {len(codes)}只...', flush=True)
for idx, code in enumerate(codes):
    if idx % 50 == 0: print(f'  {idx}/{len(codes)}', flush=True)
    sub = df[df['code']==code].sort_values('date').reset_index(drop=True)
    if len(sub) < 60: continue
    c = sub['close'].values.astype(float)
    v = sub['volume'].values.astype(float)
    for i in range(60, len(sub)-10):
        fwd = c[i+10]/c[i]-1
        records.append({
            'ret_1': c[i]/c[i-1]-1, 'ret_5': c[i]/c[i-5]-1, 'ret_10': c[i]/c[i-10]-1, 'ret_20': c[i]/c[i-20]-1,
            'ma5_r': c[i]/np.mean(c[i-5:i+1]), 'ma20_r': c[i]/np.mean(c[i-20:i+1]),
            'vol_20': np.std(c[i-20:i+1])/np.mean(c[i-20:i+1]),
            'v_ratio5': v[i]/np.mean(v[i-5:i+1]) if np.mean(v[i-5:i+1])>0 else 1,
            'label': 1 if fwd > 0 else 0,
        })

data = pd.DataFrame(records).dropna()
print(f'样本 {len(data)} ({time.time()-t0:.1f}s)', flush=True)
if len(data) < 1000: print('样本不足'); exit()

feat = ['ret_1','ret_5','ret_10','ret_20','ma5_r','ma20_r','vol_20','v_ratio5']
split = int(len(data)*0.7)
X_train, X_test = data[feat].values[:split], data[feat].values[split:]
y_train, y_test = data['label'].values[:split], data['label'].values[split:]
print(f'训练 {len(X_train)} 测试 {len(X_test)}', flush=True)
print(f'正例 {y_train.mean():.2%}', flush=True)

from sklearn.metrics import roc_auc_score

results = {}
for name, (model, params) in [
    ('Ridge', (Ridge, {'alpha':1.0})),
    ('Logistic', (LogisticRegression, {'C':1.0, 'max_iter':1000, 'random_state':42})),
    ('RandomForest', (RandomForestClassifier, {'n_estimators':200, 'max_depth':8, 'n_jobs':-1, 'random_state':42, 'class_weight':'balanced'})),
    ('LightGBM', (lgb.LGBMClassifier, {'n_estimators':200, 'learning_rate':0.03, 'num_leaves':24, 'max_depth':5, 'feature_fraction':0.7, 'reg_alpha':0.05, 'reg_lambda':0.1, 'is_unbalance':True, 'verbose':-1, 'random_state':42, 'n_jobs':-1})),
]:
    tr = time.time()
    m = model(**params)
    m.fit(X_train, y_train)
    if name == 'Ridge':
        yp = m.predict(X_test)
        yp = (yp - yp.min()) / (yp.max() - yp.min() + 1e-9)
    elif hasattr(m, 'predict_proba'):
        yp = m.predict_proba(X_test)[:, 1]
    else:
        yp = m.predict(X_test)
    auc = roc_auc_score(y_test, yp)
    results[name] = {'auc': round(auc, 4), 'time': round(time.time()-tr, 1)}
    print(f'  {name:12s} AUC={auc:.4f} 耗时{time.time()-tr:.1f}s', flush=True)

print(f'\n{"="*60}', flush=True)
print('模型对比汇总', flush=True)
print(f'{"模型":<12s} | {"AUC":>6s} | {"耗时":>6s}', flush=True)
print('-'*30, flush=True)
for name, res in sorted(results.items(), key=lambda x: x[1]['auc'], reverse=True):
    print(f'{name:<12s} | {res["auc"]:.4f} | {res["time"]:>5.1f}s', flush=True)

print(f'\n总耗时: {time.time()-t0:.1f}s', flush=True)