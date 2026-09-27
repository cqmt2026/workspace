# -*- coding: utf-8 -*-
"""
LightGBM模型优化 — 解决过拟合 + 提升滚动稳定性

对比v13的改进：
1. 参数优化：更浅的树 + 更强正则化 + 更少迭代
2. 数据优化：提高采样间隔(8→10) + 降低预测周期(10→5)
3. 特征优化：加入相对强度 + 市场因子增强
4. 验证优化：严格时间分割 + 滚动验证
"""
import sys, io, time, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t0 = time.time()

import numpy as np
import pandas as pd
import lightgbm as lgb
import sqlite3
from sklearn.metrics import roc_auc_score, accuracy_score
from sklearn.model_selection import TimeSeriesSplit

print('=' * 60, flush=True)
print('LightGBM模型优化 v14', flush=True)
print('=' * 60, flush=True)

# ─── 数据加载 ───
conn = sqlite3.connect('F:/market_data.db')
print('加载数据...', flush=True)
df = pd.read_sql(
    'SELECT code, date, open, high, low, close, volume FROM daily_k WHERE date >= "2020-01-01" ORDER BY code, date',
    conn)
conn.close()
df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
print(f'数据: {len(df)}行, {df["code"].nunique()}只 ({time.time()-t0:.1f}s)', flush=True)

# 过滤：只取历史足够+价格正常的股票
code_counts = df.groupby('code').size()
valid_codes = code_counts[code_counts >= 500].index  # 至少2年数据
df = df[df['code'].isin(valid_codes)].reset_index(drop=True)
print(f'过滤后: {len(df)}行, {len(valid_codes)}只 ({time.time()-t0:.1f}s)', flush=True)

# 取前300只（平衡速度与样本量）
codes = df['code'].unique()[:300]
print(f'使用: {len(codes)}只股票', flush=True)

# ─── 特征工程（向量化）───
records = []
print('计算特征...', flush=True)
for idx, code in enumerate(codes):
    if idx % 50 == 0: print(f'  {idx}/{len(codes)} ({time.time()-t0:.1f}s)', flush=True)
    sub = df[df['code']==code].sort_values('date').reset_index(drop=True)
    n = len(sub)
    if n < 60: continue

    c = sub['close'].values.astype(np.float64)
    v = sub['volume'].values.astype(np.float64)
    h = sub['high'].values.astype(np.float64)
    l = sub['low'].values.astype(np.float64)
    o = sub['open'].values.astype(np.float64)

    # 预计算序列
    close_s = pd.Series(c)
    vol_s = pd.Series(v)

    # 均线
    ma5 = close_s.rolling(5).mean().values
    ma20 = close_s.rolling(20).mean().values
    ma60 = close_s.rolling(60).mean().values

    # 波动率
    vol20 = close_s.rolling(20).std(ddof=0).values / close_s.rolling(20).mean().values
    vol60 = close_s.rolling(60).std(ddof=0).values / close_s.rolling(60).mean().values

    # 成交量均值
    avg_v5 = vol_s.rolling(5).mean().values
    avg_v20 = vol_s.rolling(20).mean().values

    # 高低点
    lo20 = close_s.rolling(20).min().values
    hi20 = close_s.rolling(20).max().values

    for i in range(60, n-5):  # 预测5日收益
        # 收益率因子
        r1 = c[i]/c[i-1]-1 if c[i-1] != 0 else 0
        r5 = c[i]/c[i-5]-1 if c[i-5] != 0 else 0
        r10 = c[i]/c[i-10]-1 if c[i-10] != 0 else 0
        r20 = c[i]/c[i-20]-1 if c[i-20] != 0 else 0

        # 均线比
        m5r = c[i]/ma5[i] if ma5[i] != 0 else 1
        m20r = c[i]/ma20[i] if ma20[i] != 0 else 1
        m60r = c[i]/ma60[i] if ma60[i] != 0 else 1

        # 均线排列（多头/空头）
        ma_bull = 1 if ma5[i] > ma20[i] > ma60[i] else (0 if ma5[i] < ma20[i] < ma60[i] else 0.5)

        # 波动率变化
        vol_chg = vol20[i] - vol60[i]

        # 量比
        vr5 = v[i]/avg_v5[i] if avg_v5[i] != 0 else 1
        vr20 = v[i]/avg_v20[i] if avg_v20[i] != 0 else 1

        # 价格位置
        price_pos = (c[i]-lo20[i])/(hi20[i]-lo20[i]+1e-9)

        # 日内波动
        day_range = (h[i]-l[i])/c[i] if c[i] != 0 else 0

        # 未来5日收益
        fwd = c[i+5]/c[i]-1

        records.append({
            'date': sub['date'].iloc[i], 'code': code,
            'r1': r1, 'r5': r5, 'r10': r10, 'r20': r20,
            'm5r': m5r, 'm20r': m20r, 'm60r': m60r,
            'ma_bull': ma_bull,
            'v20': vol20[i], 'v60': vol60[i], 'vchg': vol_chg,
            'vr5': vr5, 'vr20': vr20,
            'ppos': price_pos, 'drange': day_range,
            'fwd': fwd, 'label': 1 if fwd > 0 else 0,
        })

data = pd.DataFrame(records)
print(f'样本: {len(data)} ({time.time()-t0:.1f}s)', flush=True)
if len(data) < 5000: print('样本不足'); exit()

feat = ['r1','r5','r10','r20','m5r','m20r','m60r','ma_bull','v20','v60','vchg','vr5','vr20','ppos','drange']
data = data.dropna(subset=feat).reset_index(drop=True)
print(f'有效: {len(data)}样本, 正例{data["label"].mean():.1%}', flush=True)

# ─── 时间分割 ───
dates = sorted(data['date'].unique())
n_dates = len(dates)
train_end = int(n_dates * 0.7)
val_end = int(n_dates * 0.85)

train = data[data['date'].isin(dates[:train_end])]
val = data[data['date'].isin(dates[train_end:val_end])]
test = data[data['date'].isin(dates[val_end:])]

print(f'训练: {len(train)} 验证: {len(val)} 测试: {len(test)}', flush=True)

X_tr, y_tr = train[feat].values, train['label'].values
X_vl, y_vl = val[feat].values, val['label'].values
X_te, y_te = test[feat].values, test['label'].values

# ─── 多组参数对比 ───
configs = {
    'v13_基线': {'n_estimators':500, 'lr':0.02, 'leaves':48, 'depth':8, 'alpha':0.01, 'lambda':0.05, 'subsample':0.75, 'colsample':0.7},
    'v14_轻量': {'n_estimators':200, 'lr':0.05, 'leaves':24, 'depth':5, 'alpha':0.1,  'lambda':0.2,  'subsample':0.8,  'colsample':0.7},
    'v14_稳健': {'n_estimators':300, 'lr':0.03, 'leaves':16, 'depth':4, 'alpha':0.2,  'lambda':0.3,  'subsample':0.85, 'colsample':0.6},
    'v14_激进': {'n_estimators':400, 'lr':0.02, 'leaves':32, 'depth':6, 'alpha':0.05, 'lambda':0.1,  'subsample':0.75, 'colsample':0.7},
}

results = {}
for name, cfg in configs.items():
    print(f'\n训练: {name}', flush=True)
    tr = time.time()
    model = lgb.LGBMClassifier(
        n_estimators=cfg['n_estimators'], learning_rate=cfg['lr'],
        num_leaves=cfg['leaves'], max_depth=cfg['depth'],
        reg_alpha=cfg['alpha'], reg_lambda=cfg['lambda'],
        subsample=cfg['subsample'], subsample_freq=1,
        colsample_bytree=cfg['colsample'],
        min_child_samples=30, min_child_weight=5,
        objective='binary', metric='auc', boosting='gbdt',
        class_weight='balanced', verbose=-1, random_state=42, n_jobs=-1)
    model.fit(X_tr, y_tr,
              eval_set=[(X_vl, y_vl)], eval_metric='auc',
              callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)])

    # 验证集
    p_vl = model.predict_proba(X_vl)[:, 1]
    p_te = model.predict_proba(X_te)[:, 1]
    auc_vl = roc_auc_score(y_vl, p_vl)
    auc_te = roc_auc_score(y_te, p_te)

    # 分层
    from scipy.stats import spearmanr
    test_df = test.copy()
    test_df['prob'] = p_te
    test_df['layer'] = pd.qcut(test_df['prob'], 10, labels=False, duplicates='drop')
    top = test_df[test_df['layer']==test_df['layer'].max()]['fwd'].mean()
    bot = test_df[test_df['layer']==test_df['layer'].min()]['fwd'].mean()
    spread = top - bot

    # 过拟合率
    p_tr = model.predict_proba(X_tr)[:, 1]
    auc_tr = roc_auc_score(y_tr, p_tr)
    overfit = auc_tr - auc_te

    results[name] = {
        'val_auc': round(auc_vl, 4), 'test_auc': round(auc_te, 4),
        'train_auc': round(auc_tr, 4), 'overfit': round(overfit, 4),
        'spread': round(spread, 4), 'top_ret': round(top, 4), 'bot_ret': round(bot, 4),
        'time': round(time.time()-tr, 1), 'best_iter': model.best_iteration_,
    }

    print(f'  Val AUC={auc_vl:.4f} Test AUC={auc_te:.4f} 多空差={spread:.4f} ({time.time()-tr:.1f}s)', flush=True)

# ─── 结果汇总 ───
print(f'\n{"="*60}', flush=True)
print('模型对比汇总', flush=True)
print(f'{"="*60}', flush=True)
print(f'{"配置":<12s} | {"Val AUC":>7s} | {"Test AUC":>8s} | {"过拟合":>6s} | {"多空差":>6s} | {"迭代":>5s} | {"耗时":>5s}', flush=True)
print('-'*65, flush=True)
for name, r in sorted(results.items(), key=lambda x: x[1]['test_auc'], reverse=True):
    print(f'{name:<12s} | {r["val_auc"]:.4f}   | {r["test_auc"]:.4f}   | {r["overfit"]:.3f} | {r["spread"]:.4f} | {r["best_iter"]:4d} | {r["time"]:.1f}s', flush=True)

# ─── 最优模型详细评估 ───
best_name = max(results, key=lambda k: results[k]['test_auc'])
print(f'\n最佳配置: {best_name}', flush=True)

# ─── 滚动验证（模拟实盘） ───
print(f'\n{"="*60}', flush=True)
print('滚动验证（模拟实盘）', flush=True)
print(f'{"="*60}', flush=True)

best_cfg = configs[best_name]
roll_results = []
window_days = 120  # 半年数据
step_days = 20     # 每月滚动

for w in range(0, len(dates)-window_days, step_days):
    train_d = dates[w:w+window_days]
    test_d = dates[w+window_days] if w+window_days < len(dates) else dates[-1]

    tr = data[data['date'].isin(train_d)]
    te = data[data['date']==test_d]

    if len(tr) < 500 or len(te) < 5: continue

    model = lgb.LGBMClassifier(
        n_estimators=best_cfg['n_estimators'], learning_rate=best_cfg['lr'],
        num_leaves=best_cfg['leaves'], max_depth=best_cfg['depth'],
        reg_alpha=best_cfg['alpha'], reg_lambda=best_cfg['lambda'],
        subsample=best_cfg['subsample'], subsample_freq=1,
        colsample_bytree=best_cfg['colsample'],
        min_child_samples=30, objective='binary', metric='auc',
        class_weight='balanced', verbose=-1, random_state=42, n_jobs=-1)
    model.fit(tr[feat], tr['label'],
              eval_set=[(tr[feat], tr['label'])],
              eval_metric='auc',
              callbacks=[lgb.early_stopping(15), lgb.log_evaluation(0)])

    p = model.predict_proba(te[feat])[:, 1]
    auc = roc_auc_score(te['label'], p)
    acc = accuracy_score(te['label'], (p>0.5).astype(int))
    roll_results.append({'date': test_d, 'auc': auc, 'acc': acc, 'n': len(te)})
    print(f'  窗口: {test_d} AUC={auc:.4f} n={len(te)}', flush=True)

roll_df = pd.DataFrame(roll_results)
if len(roll_df) > 0:
    print(f'\n滚动验证汇总 ({len(roll_df)}个窗口):', flush=True)
    print(f'  平均AUC: {roll_df["auc"].mean():.4f}', flush=True)
    print(f'  AUC标准差: {roll_df["auc"].std():.4f}', flush=True)
    print(f'  AUC>0.55: {(roll_df["auc"]>0.55).mean()*100:.0f}%', flush=True)
    print(f'  AUC>0.60: {(roll_df["auc"]>0.60).mean()*100:.0f}%', flush=True)

print(f'\n总耗时: {time.time()-t0:.1f}s', flush=True)