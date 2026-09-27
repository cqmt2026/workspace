# -*- coding: utf-8 -*-
"""
ML回归模型 — 预测5天涨幅%（不是涨/跌分类）

核心改变：
  分类模型 → predict_proba → 均值0.01 → 废了
  回归模型 → predict → 均值0.5% → 直接可用

输出：每只股票的预期5天涨幅%，转成0~10分评分
"""
import sys, io, time, os, pickle, warnings
from pathlib import Path
warnings.filterwarnings('ignore')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t0 = time.time()

import numpy as np
import pandas as pd
import sqlite3
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, r2_score

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
DB = r'F:\market_data.db'
SAMPLE_SIZE = 1000
PRED_STEP = 5

print('ML Regression Training v1', flush=True)
print('='*60, flush=True)

conn = sqlite3.connect(DB)
all_codes = [r[0] for r in conn.execute(
    "SELECT DISTINCT code FROM daily_k WHERE code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%'"
).fetchall()]
st_codes = set(r[0] for r in conn.execute("SELECT code FROM stock_st_status WHERE is_st=1").fetchall())
all_codes = [c for c in all_codes if c not in st_codes][:SAMPLE_SIZE]
print(f'Stock pool: {len(all_codes)}', flush=True)

def extract_features(sub):
    """提取特征 + 回归标签（5天涨幅%）"""
    n = len(sub)
    if n < 70: return [], []
    
    sub['volume'] = pd.to_numeric(sub['volume'], errors='coerce').fillna(0)
    c = sub['close'].values.astype(np.float64)
    v = sub['volume'].values.astype(np.float64)
    h = sub['high'].values.astype(np.float64)
    l = sub['low'].values.astype(np.float64)
    
    close_s = pd.Series(c)
    ma5 = close_s.rolling(5).mean().values
    ma20 = close_s.rolling(20).mean().values
    ma60 = close_s.rolling(60).mean().values if n >= 65 else np.full(n, np.nan)
    
    delta = np.diff(c); gain = np.maximum(delta, 0); loss = -np.minimum(delta, 0)
    avg_gain = np.convolve(gain, np.ones(14)/14, mode='same')
    avg_loss = np.convolve(loss, np.ones(14)/14, mode='same')
    rs = avg_gain / np.maximum(avg_loss, 1e-9); rsi = 100 - 100 / (1 + rs)
    
    ema12 = close_s.ewm(span=12).mean().values
    ema26 = close_s.ewm(span=26).mean().values
    macd = ema12 - ema26; signal = pd.Series(macd).ewm(span=9).mean().values
    macd_hist = macd - signal
    
    bb_mid = close_s.rolling(20).mean().values
    bb_std = close_s.rolling(20).std(ddof=0).values
    
    X, y = [], []
    for i in range(65, n - PRED_STEP):
        # 回归标签：5天后的实际涨幅%（裁剪极端值）
        fwd_ret = (c[i + PRED_STEP] / c[i] - 1) * 100  # 百分比
        fwd_ret = max(-30.0, min(30.0, fwd_ret))  # 裁剪到[-30%, +30%]
        
        X.append([
            c[i]/c[i-1]-1,  # ret_1d
            c[i]/c[i-5]-1,  # ret_5d
            c[i]/c[i-10]-1, # ret_10d
            c[i]/c[i-20]-1, # ret_20d
            c[i]/ma5[i] if ma5[i]!=0 else 1,
            c[i]/ma20[i] if ma20[i]!=0 else 1,
            np.std(c[i-20:i+1])/np.mean(c[i-20:i+1]) if np.mean(c[i-20:i+1])>0 else 0,
            v[i]/np.mean(v[i-5:i+1]) if np.mean(v[i-5:i+1])>0 else 1,
            (c[i]-np.min(l[i-20:i+1]))/(np.max(h[i-20:i+1])-np.min(l[i-20:i+1])+1e-9),
            (c[i]/c[i-1]-1) * (v[i]/np.mean(v[i-5:i+1]) - 1) if np.mean(v[i-5:i+1])>0 else 0,
            np.std(c[i-5:i+1]) / np.std(c[i-20:i+1]) if np.std(c[i-20:i+1])>0 else 1,
            c[i]/ma60[i]-1 if not np.isnan(ma60[i]) and ma60[i]!=0 else 0,
            rsi[i]/100 if not np.isnan(rsi[i]) else 0.5,
            macd_hist[i] / np.maximum(np.abs(macd_hist[max(0,i-20):i+1]).mean(), 0.001) if i>=20 else 0,
            (c[i] - bb_mid[i]) / np.maximum(bb_std[i] * 2, 0.01) if not np.isnan(bb_std[i]) else 0,
            bb_std[i] / np.maximum(bb_mid[i], 0.01) if not np.isnan(bb_std[i]) else 0,
            np.max(c[i-5:i+1]) / np.min(c[i-5:i+1]) - 1,
        ])
        y.append(fwd_ret)
    
    return X, y


# Build dataset
print('Building dataset...', flush=True)
all_X, all_y = [], []
X_arr, y_arr = None, None

for idx, code in enumerate(all_codes):
    if idx % 200 == 0: print(f'  {idx}/{len(all_codes)} ({time.time()-t0:.1f}s)', flush=True)
    sub = pd.read_sql(
        'SELECT date, close, volume, high, low FROM daily_k WHERE code=? ORDER BY date DESC LIMIT 120',
        conn, params=(code,))
    if len(sub) < 70: continue
    sub = sub.sort_values('date').reset_index(drop=True)
    lx, ly = extract_features(sub)
    if lx:
        all_X.extend(lx)
        all_y.extend(ly)
    
    # chunked to avoid OOM
    if (idx + 1) % 100 == 0 and all_X:
        chunk_X = np.array(all_X, dtype=np.float32)
        chunk_y = np.array(all_y, dtype=np.float32)
        if X_arr is None:
            X_arr, y_arr = chunk_X, chunk_y
        else:
            X_arr = np.vstack([X_arr, chunk_X])
            y_arr = np.concatenate([y_arr, chunk_y])
        del chunk_X, chunk_y, all_X, all_y
        all_X, all_y = [], []

# remaining
if all_X:
    chunk_X = np.array(all_X, dtype=np.float32)
    chunk_y = np.array(all_y, dtype=np.float32)
    if X_arr is None:
        X_arr, y_arr = chunk_X, chunk_y
    else:
        X_arr = np.vstack([X_arr, chunk_X])
        y_arr = np.concatenate([y_arr, chunk_y])
    del chunk_X, chunk_y

print(f'Samples: {len(y_arr)} ({time.time()-t0:.1f}s)', flush=True)
print(f'Label stats: mean={np.mean(y_arr):.2f}% std={np.std(y_arr):.2f}% min={np.min(y_arr):.2f}% max={np.max(y_arr):.2f}%', flush=True)

# Train/Val/Test split
from sklearn.model_selection import train_test_split
X_tr, X_te, y_tr, y_te = train_test_split(X_arr, y_arr, test_size=0.2, random_state=42, shuffle=False)
X_tr, X_vl, y_tr, y_vl = train_test_split(X_tr, y_tr, test_size=0.15, random_state=42, shuffle=False)

# LightGBM Regression
print(f'\n{"="*60}', flush=True)
print('Training LightGBM Regressor...', flush=True)
model = lgb.LGBMRegressor(
    n_estimators=300, learning_rate=0.03, num_leaves=24, max_depth=5,
    feature_fraction=0.7, subsample=0.8, reg_alpha=0.1, reg_lambda=0.2,
    verbose=-1, random_state=42, n_jobs=-1,
    min_child_samples=20, min_split_gain=0.01,
    objective='regression', metric='mae')
model.fit(X_tr, y_tr, eval_set=[(X_vl, y_vl)],
          callbacks=[lgb.early_stopping(30), lgb.log_evaluation(0)])

p_te = model.predict(X_te)
mae = mean_absolute_error(y_te, p_te)
r2 = r2_score(y_te, p_te)
# 计算方向准确率（预测涨 vs 实际涨）
direction_acc = np.mean((p_te > 0) == (y_te > 0))
print(f'MAE: {mae:.3f}%', flush=True)
print(f'R2: {r2:.4f}', flush=True)
print(f'Direction accuracy: {direction_acc:.1%}', flush=True)

# Save model
import joblib
model_path = WORK_DIR / 'quant_ml' / 'data' / 'models' / 'lgbm_regressor.pkl'
joblib.dump(model, model_path)
print(f'Model saved: {model_path}', flush=True)

# Generate predictions for all stocks
print(f'\nGenerating predictions for {len(all_codes)} stocks...', flush=True)
conn2 = sqlite3.connect(DB)
predictions = {}
for idx, code in enumerate(all_codes):
    if idx % 300 == 0: print(f'  {idx}/{len(all_codes)} ({time.time()-t0:.1f}s)', flush=True)
    sub = pd.read_sql(
        'SELECT date, close, volume, high, low FROM daily_k WHERE code=? ORDER BY date DESC LIMIT 120',
        conn2, params=(code,))
    if len(sub) < 70: continue
    sub['volume'] = pd.to_numeric(sub['volume'], errors='coerce').fillna(0)
    c = sub['close'].values.astype(np.float64)
    v = sub['volume'].values.astype(np.float64)
    h = sub['high'].values.astype(np.float64)
    l = sub['low'].values.astype(np.float64)
    n = len(c)
    i = n - 1
    
    close_s = pd.Series(c)
    ma5 = close_s.rolling(5).mean().values
    ma20 = close_s.rolling(20).mean().values
    ma60 = close_s.rolling(60).mean().values[i]
    
    delta = np.diff(c); gain = np.maximum(delta, 0); loss = -np.minimum(delta, 0)
    avg_gain = np.convolve(gain, np.ones(14)/14, mode='same')
    avg_loss = np.convolve(loss, np.ones(14)/14, mode='same')
    rs = avg_gain / np.maximum(avg_loss, 1e-9); rsi_arr = 100 - 100 / (1 + rs)
    rsi_v = rsi_arr[i] if i < len(rsi_arr) else 0.5
    
    ema12 = close_s.ewm(span=12).mean().values
    ema26 = close_s.ewm(span=26).mean().values
    macd = ema12 - ema26; signal = pd.Series(macd).ewm(span=9).mean().values
    macd_hist = macd - signal
    mh_v = macd_hist[i] / np.maximum(np.abs(macd_hist[max(0,i-20):i+1]).mean(), 0.001)
    
    bb_mid = close_s.rolling(20).mean().values
    bb_std = close_s.rolling(20).std(ddof=0).values
    bb_pos = (c[i] - bb_mid[i]) / np.maximum(bb_std[i] * 2, 0.01) if not np.isnan(bb_std[i]) else 0
    bb_width = bb_std[i] / np.maximum(bb_mid[i], 0.01) if not np.isnan(bb_std[i]) else 0
    
    fv = np.array([[
        c[i]/c[i-1]-1, c[i]/c[i-5]-1, c[i]/c[i-10]-1,
        c[i]/c[i-20]-1,
        c[i]/ma5[i] if ma5[i]!=0 else 1,
        c[i]/ma20[i] if ma20[i]!=0 else 1,
        np.std(c[i-20:i+1])/np.mean(c[i-20:i+1]) if np.mean(c[i-20:i+1])>0 else 0,
        v[i]/np.mean(v[i-5:i+1]) if np.mean(v[i-5:i+1])>0 else 1,
        (c[i]-np.min(l[i-20:i+1]))/(np.max(h[i-20:i+1])-np.min(l[i-20:i+1])+1e-9),
        (c[i]/c[i-1]-1) * (v[i]/np.mean(v[i-5:i+1]) - 1) if np.mean(v[i-5:i+1])>0 else 0,
        np.std(c[i-5:i+1]) / np.std(c[i-20:i+1]) if np.std(c[i-20:i+1])>0 else 1,
        c[i]/ma60-1 if not np.isnan(ma60) and ma60!=0 else 0,
        rsi_v/100,
        mh_v,
        bb_pos, bb_width,
        np.max(c[i-5:i+1]) / np.min(c[i-5:i+1]) - 1,
    ]], dtype=np.float32)
    try:
        pred_ret = float(model.predict(fv)[0])
        predictions[code] = pred_ret  # 预期5天涨幅%
    except:
        predictions[code] = 0.0

conn2.close()
conn.close()

# 转成0~10分评分
rets = np.array(list(predictions.values()))
print(f'\n{"="*60}', flush=True)
print(f'Predictions: {len(predictions)} stocks', flush=True)
print(f'Return range: min={rets.min():.2f}% max={rets.max():.2f}% mean={rets.mean():.2f}%', flush=True)
print(f'Percentiles:', flush=True)
for p in [10, 25, 50, 75, 90, 95, 99]:
    print(f'  P{p}: {np.percentile(rets, p):.2f}%', flush=True)

# 评分映射：预期涨幅 → 0~10分
# 阈值基于训练集标签分布
r_min, r_max = -5.0, 5.0  # 预期收益在-5%~+5%之间
scores = {}
for code, ret in predictions.items():
    if ret <= -2.0:
        scores[code] = 0.0
    elif ret >= 4.0:
        scores[code] = 10.0
    else:
        scores[code] = round((ret + 2.0) / 6.0 * 10.0, 1)

# 保存
out_path = WORK_DIR / 'scripts' / 'ml_regression_pred.pkl'
with open(out_path, 'wb') as f:
    pickle.dump({'returns': predictions, 'scores': scores}, f)
print(f'\nSaved to: {out_path}', flush=True)

# 验证结果
print(f'\n{"="*60}', flush=True)
print('Results:', flush=True)
print(f'  预期涨幅>0: {sum(1 for v in rets if v > 0)}只 ({sum(1 for v in rets if v > 0)/len(rets)*100:.1f}%)', flush=True)
print(f'  预期涨幅>2%: {sum(1 for v in rets if v > 2)}只', flush=True)
print(f'  预期涨幅>5%: {sum(1 for v in rets if v > 5)}只', flush=True)
print(f'  评分>=8分: {sum(1 for s in scores.values() if s >= 8)}只', flush=True)
print(f'  评分>=6分: {sum(1 for s in scores.values() if s >= 6)}只', flush=True)
print(f'  评分>=4分: {sum(1 for s in scores.values() if s >= 4)}只', flush=True)

print(f'\nTop 20 (by expected return):', flush=True)
for code, ret in sorted(predictions.items(), key=lambda x: -x[1])[:20]:
    s = scores[code]
    print(f'  {code}: 预期+{ret:.2f}% 评分={s}', flush=True)

print(f'\nBottom 10:', flush=True)
for code, ret in sorted(predictions.items(), key=lambda x: x[1])[:10]:
    s = scores[code]
    print(f'  {code}: 预期{ret:.2f}% 评分={s}', flush=True)

print(f'\nTime: {time.time()-t0:.1f}s', flush=True)