import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t0 = time.time()
print('滚动训练', flush=True)
print('='*60, flush=True)

import numpy as np
import pandas as pd
import lightgbm as lgb
import sqlite3

print(f'导入 {time.time()-t0:.1f}s', flush=True)

conn = sqlite3.connect('F:/market_data.db')
print('查询DB...', flush=True)
df = pd.read_sql(
    'SELECT code, date, close, volume FROM daily_k WHERE date >= "2024-01-01" ORDER BY code, date',
    conn)
conn.close()
df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
print(f'数据 {len(df)}行 {df["code"].nunique()}只 ({time.time()-t0:.1f}s)', flush=True)

# 取前100只股票
codes = df['code'].unique()[:100]
records = []
print(f'计算特征 {len(codes)}只...', flush=True)
for idx, code in enumerate(codes):
    if idx % 25 == 0: print(f'  {idx}/{len(codes)}', flush=True)
    sub = df[df['code']==code].sort_values('date').reset_index(drop=True)
    if len(sub) < 60: continue
    c = sub['close'].values.astype(float)
    v = sub['volume'].values.astype(float)
    for i in range(60, len(sub)-10):
        fwd = c[i+10]/c[i]-1
        records.append({
            'date': sub['date'].iloc[i], 'code': code,
            'ret_1': c[i]/c[i-1]-1, 'ret_5': c[i]/c[i-5]-1,
            'ma5_r': c[i]/np.mean(c[i-5:i+1]), 'ma20_r': c[i]/np.mean(c[i-20:i+1]),
            'vol_20': np.std(c[i-20:i+1])/np.mean(c[i-20:i+1]),
            'v_ratio5': v[i]/np.mean(v[i-5:i+1]) if np.mean(v[i-5:i+1])>0 else 1,
            'label': 1 if fwd > 0 else 0,
        })

data = pd.DataFrame(records)
print(f'样本 {len(data)} ({time.time()-t0:.1f}s)', flush=True)
if len(data) < 1000: print('样本不足'); exit()

feat = ['ret_1','ret_5','ma5_r','ma20_r','vol_20','v_ratio5']
dates = sorted(data['date'].unique())
window, step = 120, 20
n_windows = (len(dates) - window) // step
print(f'交易日 {len(dates)}个, 窗口{window}步长{step}, 约{n_windows}个窗口', flush=True)

results = []
for w in range(n_windows):
    train_end = dates[w * step + window]
    train_start = dates[w * step]
    test_date = dates[w * step + window + 1] if w * step + window + 1 < len(dates) else dates[-1]

    train = data[(data['date']>=train_start) & (data['date']<train_end)]
    test = data[data['date']==test_date]

    if len(train) < 200 or len(test) < 5: continue

    model = lgb.LGBMClassifier(
        n_estimators=150, learning_rate=0.05, num_leaves=16, max_depth=4,
        feature_fraction=0.7, reg_alpha=0.05, reg_lambda=0.1, is_unbalance=True,
        verbose=-1, random_state=42, n_jobs=-1)
    model.fit(train[feat], train['label'])

    y_prob = model.predict_proba(test[feat])[:, 1]
    y_pred = model.predict(test[feat])
    from sklearn.metrics import roc_auc_score, accuracy_score
    auc = roc_auc_score(test['label'], y_prob)
    acc = accuracy_score(test['label'], y_pred)

    results.append({
        'window': w, 'train_start': train_start, 'train_end': train_end, 'test_date': test_date,
        'n_train': len(train), 'n_test': len(test), 'auc': round(auc, 4), 'accuracy': round(acc, 4),
        'positive_rate': round(test['label'].mean(), 3),
    })

    if w % 5 == 0:
        print(f'  窗口{w:3d}: {train_start}~{train_end}->{test_date} AUC={auc:.4f} n={len(test)}', flush=True)

res_df = pd.DataFrame(results)
print(f'\n{"="*60}', flush=True)
print(f'滚动训练汇总 ({len(res_df)}个窗口)', flush=True)
print(f'平均AUC: {res_df["auc"].mean():.4f} 标准差: {res_df["auc"].std():.4f}', flush=True)
print(f'AUC>0.55: {(res_df["auc"]>0.55).mean()*100:.0f}% AUC>0.60: {(res_df["auc"]>0.60).mean()*100:.0f}%', flush=True)

print(f'\n总耗时: {time.time()-t0:.1f}s', flush=True)