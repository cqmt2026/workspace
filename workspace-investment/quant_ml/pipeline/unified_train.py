import sys, io, time, os, pickle, warnings, argparse, json, glob, shutil
from pathlib import Path
warnings.filterwarnings('ignore')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t0 = time.time()

# 启动时备份当前生产模型
BACKUP_PATH = MODEL_DIR / 'lgbm_unified_backup.pkl'
if MODEL_PATH.exists():
    try:
        shutil.copy2(MODEL_PATH, BACKUP_PATH)
        print(f'[Backup] 已备份当前模型到 lgbm_unified_backup.pkl', flush=True)
    except Exception as e:
        print(f'[Backup] 备份失败: {e}', flush=True)

# 训练完成后的恢复逻辑（若新模型AUC不提升则回滚）
def _restore_if_regression(new_auc, threshold_auc=0.880):
    """若新模型AUC未达到阈值，用备份恢复生产模型"""
    import json as _json
    if BACKUP_PATH.exists() and new_auc < threshold_auc:
        print(f'[Rollback] 新模型AUC={new_auc:.4f} < {threshold_auc:.4f}，回滚到备份', flush=True)
        shutil.copy2(BACKUP_PATH, MODEL_PATH)
        # 清理低AUC模型
        bad_path = MODEL_DIR / 'lgbm_unified_bad.pkl'
        if bad_path.exists():
            bad_path.unlink()
        MODEL_PATH.rename(bad_path)
        # 恢复后再次copy备份到生产
        shutil.copy2(BACKUP_PATH, MODEL_PATH)
        print(f'[Rollback] 生产模型已恢复', flush=True)
        return True
    return False

parser = argparse.ArgumentParser()
parser.add_argument('--quick', action='store_true', help='Quick: 2000 stocks, no MSTNN')
parser.add_argument('--no-mstnn', action='store_true', help='Skip MSTNN training')
args = parser.parse_args()

print('Unified Training v4', flush=True)
if args.quick: print('Quick mode (2000 stocks, no MSTNN)', flush=True)
print('=' * 60, flush=True)

import numpy as np
import pandas as pd
import sqlite3
import lightgbm as lgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
import joblib

# ─── Config ─────────────────────────────────────────────────────────
WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
DB = r'F:\market_data.db'
SAMPLE_SIZE = 2000 if args.quick else 5000
WINDOW_SIZE = 65
PRED_STEP = 5
MSTNN_SAMPLE_SIZE = 0 if (args.quick or args.no_mstnn) else 500
FEATURE_CHANNELS = 4
CHUNK_SIZE = 50       # 数据构建分块
PRED_CHUNK = 200      # 预测分块
MODEL_DIR = WORK_DIR / 'quant_ml' / 'data' / 'models'
MODEL_PATH = MODEL_DIR / 'lgbm_unified.pkl'
REGISTRY_PATH = MODEL_DIR / 'model_registry.json'
PROB_PATH = WORK_DIR / 'scripts' / 'ml_latest_prob.pkl'
KEEP = {'lgbm_unified.pkl', 'mstnn_model.pth', 'model_registry.json'}

# ─── 特征名称（16维，必须与predict_single完全一致） ─────────────
FEAT_NAMES = [
    'ret_1d', 'ret_5d', 'ret_10d',
    'ma5_ratio', 'ma20_ratio',
    'vol_20d', 'volume_ratio', 'stoch_pos',
    'vol_price_coord', 'vol_ratio_change',
    'ma60_ratio', 'rsi_14d',
    'macd_hist_norm', 'bb_pos', 'bb_width',
    'amp_5d',
]
assert len(FEAT_NAMES) == 16, f'Expected 16 features, got {len(FEAT_NAMES)}'

# ─── DB连接 + 股票池 ──────────────────────────────────────────────
conn = sqlite3.connect(DB)
all_codes_raw = [r[0] for r in conn.execute(
    "SELECT DISTINCT code FROM daily_k WHERE code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%'"
).fetchall()]
st_codes = set(r[0] for r in conn.execute("SELECT code FROM stock_st_status WHERE is_st=1").fetchall())
# 打乱顺序取SAMPLE_SIZE只，避免按字母排序只取到sh.600开头的股票
import random
all_codes_clean = [c for c in all_codes_raw if c not in st_codes]
random.seed(42)
random.shuffle(all_codes_clean)
all_codes = all_codes_clean[:SAMPLE_SIZE]
print(f'Stock pool: {len(all_codes)} (shuffled from {len(all_codes_clean)} total)', flush=True)


# ─── 辅助函数 ──────────────────────────────────────────────────────
def _build_feat_row(c, v, h, l, i, close_s, ma5, ma20, ma60, rsi_arr, macd_hist, bb_mid, bb_std):
    """构造单行16维特征向量"""
    rsi_v = rsi_arr[i] / 100 if i < len(rsi_arr) and not np.isnan(rsi_arr[i]) else 0.5
    mh_v = macd_hist[i] / max(np.abs(macd_hist[max(0, i-20):i+1]).mean(), 0.001)
    bw = bb_std[i] / max(bb_mid[i], 0.01) if not np.isnan(bb_std[i]) else 0
    bp = (c[i] - bb_mid[i]) / max(bb_std[i] * 2, 0.01) if not np.isnan(bb_std[i]) else 0
    return [
        c[i]/c[i-1]-1,
        c[i]/c[i-5]-1,
        c[i]/c[i-10]-1,
        c[i]/ma5[i] if ma5[i] != 0 else 1,
        c[i]/ma20[i] if ma20[i] != 0 else 1,
        np.std(c[i-20:i+1]) / max(np.mean(c[i-20:i+1]), 0.01),
        v[i] / max(np.mean(v[i-5:i+1]), 1),
        (c[i] - np.min(l[i-20:i+1])) / (np.max(h[i-20:i+1]) - np.min(l[i-20:i+1]) + 1e-9),
        (c[i]/c[i-1]-1) * (v[i]/max(np.mean(v[i-5:i+1]), 1) - 1),
        np.std(c[i-5:i+1]) / max(np.std(c[i-20:i+1]), 0.01),
        c[i]/ma60[i]-1 if not np.isnan(ma60[i]) and ma60[i] != 0 else 0,
        rsi_v, mh_v, bp, bw,
        max(c[i-5:i+1]) / max(min(c[i-5:i+1]), 0.01) - 1,
    ]

def load_stock_data(code, conn, limit=None):
    """从DB读取股票数据，统一处理"""
    lmt = limit or WINDOW_SIZE + PRED_STEP * 10
    sub = pd.read_sql(
        f'SELECT date, close, volume, high, low FROM daily_k WHERE code=? ORDER BY date DESC LIMIT {lmt}',
        conn, params=(code,))
    if len(sub) < WINDOW_SIZE:
        return None
    sub['volume'] = pd.to_numeric(sub['volume'], errors='coerce').fillna(0)
    return sub.sort_values('date').reset_index(drop=True)

def extract_features(sub):
    """从DataFrame中提取16维特征 + MSTNN特征，返回list"""
    n = len(sub)
    if n < WINDOW_SIZE:
        return [], [], [], [], [], []
    c = sub['close'].values.astype(np.float64)
    v = sub['volume'].values.astype(np.float64)
    h = sub['high'].values.astype(np.float64)
    l = sub['low'].values.astype(np.float64)
    close_s = pd.Series(c)
    ma5 = close_s.rolling(5).mean().values
    ma20 = close_s.rolling(20).mean().values
    ma60 = close_s.rolling(60).mean().values if n >= 65 else np.full(n, np.nan)
    # RSI
    delta = np.diff(c); gain = np.maximum(delta, 0); loss = -np.minimum(delta, 0)
    avg_g = np.convolve(gain, np.ones(14)/14, mode='same')
    avg_l = np.convolve(loss, np.ones(14)/14, mode='same')
    rsi_arr = 100 - 100 / (1 + avg_g / np.maximum(avg_l, 1e-9))
    # MACD
    ema12 = close_s.ewm(span=12).mean().values
    ema26 = close_s.ewm(span=26).mean().values
    macd_hist = (ema12 - ema26) - pd.Series(ema12 - ema26).ewm(span=9).mean().values
    # Bollinger
    bb_mid = close_s.rolling(20).mean().values
    bb_std = close_s.rolling(20).std(ddof=0).values
    # 4通道特征（用于MSTNN）
    pct = np.diff(c) / np.maximum(c[:-1], 0.01) * 100; pct = np.insert(pct, 0, 0)
    vr = v / np.maximum(np.convolve(v, np.ones(5)/5, mode='same'), 1)
    vol = (h - l) / np.maximum(c, 0.01) * 100
    vchg = np.diff(v) / np.maximum(v[:-1], 1) * 100; vchg = np.insert(vchg, 0, 0)
    feat_all = np.nan_to_num(np.column_stack([pct, vr, vol, vchg]), nan=0.0, posinf=5.0, neginf=-5.0)

    lgbm_X, lgbm_y = [], []
    m5, m10, m20, my = [], [], [], []
    for i in range(WINDOW_SIZE, n - PRED_STEP):
        label = 1 if c[i + PRED_STEP] / c[i] - 1 > 0 else 0
        lgbm_X.append(_build_feat_row(c, v, h, l, i, close_s, ma5, ma20, ma60, rsi_arr, macd_hist, bb_mid, bb_std))
        lgbm_y.append(label)
        if i >= 19:
            f = feat_all[i-19:i+1].copy()
            for ch in range(FEATURE_CHANNELS):
                col = f[:, ch]; mn, sd = np.mean(col), np.std(col)
                f[:, ch] = (col - mn) / sd if sd > 1e-6 else col - mn
            m5.append(f[-5:].flatten())
            m10.append(f[-10:].flatten())
            m20.append(f.flatten())
            my.append(label)
    return lgbm_X, lgbm_y, m5, m10, m20, my

def predict_single(model, code, conn):
    """预测单只股票未来5天上涨概率"""
    sub = load_stock_data(code, conn)
    if sub is None:
        return None
    c = sub['close'].values.astype(np.float64)
    v = sub['volume'].values.astype(np.float64)
    h = sub['high'].values.astype(np.float64)
    l = sub['low'].values.astype(np.float64)
    close_s = pd.Series(c)
    ma5 = close_s.rolling(5).mean().values
    ma20 = close_s.rolling(20).mean().values
    ma60 = close_s.rolling(60).mean().values
    delta = np.diff(c); gain = np.maximum(delta, 0); loss = -np.minimum(delta, 0)
    avg_g = np.convolve(gain, np.ones(14)/14, mode='same')
    avg_l = np.convolve(loss, np.ones(14)/14, mode='same')
    rsi_arr = 100 - 100 / (1 + avg_g / np.maximum(avg_l, 1e-9))
    ema12 = close_s.ewm(span=12).mean().values
    ema26 = close_s.ewm(span=26).mean().values
    macd_hist = (ema12 - ema26) - pd.Series(ema12 - ema26).ewm(span=9).mean().values
    bb_mid = close_s.rolling(20).mean().values
    bb_std = close_s.rolling(20).std(ddof=0).values
    i = len(c) - 1
    try:
        fv = np.array([_build_feat_row(c, v, h, l, i, close_s, ma5, ma20, ma60, rsi_arr, macd_hist, bb_mid, bb_std)], dtype=np.float32)
        return float(model.predict_proba(fv)[0, 1])
    except:
        return 0.5

# ─── Phase 1: Build dataset (chunked) ─────────────────────────────
print('Building LightGBM dataset...', flush=True)
all_lgbm_X, all_lgbm_y = [], []
lgbm_X_arr, lgbm_y_arr = None, None

for idx, code in enumerate(all_codes):
    if idx % 200 == 0:
        print(f'  {idx}/{len(all_codes)} ({time.time()-t0:.1f}s)', flush=True)
    sub = load_stock_data(code, conn)
    if sub is None:
        continue
    lx, ly, _, _, _, _ = extract_features(sub)
    if lx:
        all_lgbm_X.extend(lx)
        all_lgbm_y.extend(ly)
    if (idx + 1) % CHUNK_SIZE == 0 and all_lgbm_X:
        cx = np.array(all_lgbm_X, dtype=np.float32)
        cy = np.array(all_lgbm_y, dtype=np.int8)
        lgbm_X_arr = cx if lgbm_X_arr is None else np.vstack([lgbm_X_arr, cx])
        lgbm_y_arr = cy if lgbm_y_arr is None else np.concatenate([lgbm_y_arr, cy])
        del cx, cy, all_lgbm_X, all_lgbm_y
        all_lgbm_X, all_lgbm_y = [], []

if all_lgbm_X:
    cx = np.array(all_lgbm_X, dtype=np.float32)
    cy = np.array(all_lgbm_y, dtype=np.int8)
    lgbm_X_arr = cx if lgbm_X_arr is None else np.vstack([lgbm_X_arr, cx])
    lgbm_y_arr = cy if lgbm_y_arr is None else np.concatenate([lgbm_y_arr, cy])
    del cx, cy
del all_lgbm_X, all_lgbm_y

n_samples = len(lgbm_y_arr) if lgbm_y_arr is not None else 0
print(f'LightGBM samples: {n_samples} ({time.time()-t0:.1f}s)', flush=True)
if n_samples < 5000:
    print(f'Not enough samples ({n_samples}), exit', flush=True)
    conn.close()
    exit()

# ─── Phase 2: Train LightGBM ─────────────────────────────────────
print(f'\n{"="*60}', flush=True)
print('Training LightGBM...', flush=True)
X_tr, X_te, y_tr, y_te = train_test_split(lgbm_X_arr, lgbm_y_arr, test_size=0.2, random_state=42, shuffle=False)
X_tr, X_vl, y_tr, y_vl = train_test_split(X_tr, y_tr, test_size=0.15, random_state=42, shuffle=False)

model = lgb.LGBMClassifier(
    n_estimators=300, learning_rate=0.03, num_leaves=24, max_depth=5,
    feature_fraction=0.7, subsample=0.8, reg_alpha=0.1, reg_lambda=0.2,
    verbose=-1, random_state=42, n_jobs=-1,
    min_child_samples=20, min_split_gain=0.01)
model.fit(X_tr, y_tr, eval_set=[(X_vl, y_vl)], eval_metric='auc',
          callbacks=[lgb.early_stopping(30), lgb.log_evaluation(0)])
auc_lgbm = roc_auc_score(y_te, model.predict_proba(X_te)[:, 1])
print(f'LightGBM: AUC={auc_lgbm:.4f} ({time.time()-t0:.1f}s)', flush=True)

# 保存模型前先备份旧模型
if MODEL_PATH.exists():
    backup = MODEL_DIR / f'lgbm_unified_bak_{int(time.time())}.pkl'
    try:
        shutil.copy2(MODEL_PATH, backup)
        print(f'Backed up old model: {backup.name}', flush=True)
    except Exception as e:
        print(f'Backup failed: {e}', flush=True)

joblib.dump(model, MODEL_PATH)
print(f'Model saved: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.0f}KB)', flush=True)

# 释放训练数据
del lgbm_X_arr, lgbm_y_arr, X_tr, X_te, y_tr, y_te, X_vl, y_vl

# ─── Phase 3: Predict all stocks ─────────────────────────────────
print(f'\nGenerating predictions for {len(all_codes)} stocks (chunked)...', flush=True)
lgbm_probs = {}
for chunk_start in range(0, len(all_codes), PRED_CHUNK):
    chunk_codes = all_codes[chunk_start:chunk_start + PRED_CHUNK]
    for code in chunk_codes:
        p = predict_single(model, code, conn)
        if p is not None:
            lgbm_probs[code] = p
    if chunk_start % 600 == 0:
        print(f'  Pred {min(chunk_start + PRED_CHUNK, len(all_codes))}/{len(all_codes)} ({time.time()-t0:.1f}s)', flush=True)
    del chunk_codes

with open(PROB_PATH, 'wb') as f:
    pickle.dump(lgbm_probs, f)
vals = list(lgbm_probs.values())
print(f'LightGBM: {len(lgbm_probs)} stocks, mean={np.mean(vals):.4f}', flush=True)
print(f'Probabilities saved!', flush=True)

# ─── Phase 4: MSTNN ──────────────────────────────────────────────
if MSTNN_SAMPLE_SIZE == 0:
    print(f'\nMSTNN skipped (--quick or --no-mstnn)', flush=True)
    auc_mstnn = None
    mstnn_probs = {}
else:
    print(f'\n{"="*60}', flush=True)
    print('Training MSTNN (streaming)...', flush=True)
    auc_mstnn = None
    mstnn_probs = {}
    try:
        import torch, torch.nn as nn, torch.optim as optim
        from torch.utils.data import DataLoader, TensorDataset

        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.c5 = nn.Sequential(nn.Conv1d(4,16,3,padding=1),nn.ReLU(),nn.MaxPool1d(2),nn.Dropout(0.3),
                    nn.Conv1d(16,32,3,padding=1),nn.ReLU(),nn.AdaptiveAvgPool1d(1))
                self.c10 = nn.Sequential(nn.Conv1d(4,16,5,padding=2),nn.ReLU(),nn.MaxPool1d(2),nn.Dropout(0.3),
                    nn.Conv1d(16,32,5,padding=2),nn.ReLU(),nn.AdaptiveAvgPool1d(1))
                self.c20 = nn.Sequential(nn.Conv1d(4,16,7,padding=3),nn.ReLU(),nn.MaxPool1d(2),nn.Dropout(0.3),
                    nn.Conv1d(16,32,7,padding=3),nn.ReLU(),nn.AdaptiveAvgPool1d(1))
                self.fc = nn.Sequential(nn.Linear(96,64),nn.ReLU(),nn.Dropout(0.3),nn.Linear(64,2))
            def forward(self, x5, x10, x20):
                x5, x10, x20 = x5.permute(0,2,1), x10.permute(0,2,1), x20.permute(0,2,1)
                return self.fc(torch.cat([self.c5(x5).squeeze(-1), self.c10(x10).squeeze(-1), self.c20(x20).squeeze(-1)], 1))

        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        net = Net().to(device)
        opt = optim.Adam(net.parameters(), lr=0.001, weight_decay=1e-4)
        crit = nn.CrossEntropyLoss()
        mstnn_codes = all_codes[:MSTNN_SAMPLE_SIZE]
        CHUNK_M = 50
        n_epochs = 5

        for ep in range(n_epochs):
            net.train()
            total_loss = 0
            n_batches = 0
            for cs in range(0, len(mstnn_codes), CHUNK_M):
                cx5, cx10, cx20, cy = [], [], [], []
                for code in mstnn_codes[cs:cs+CHUNK_M]:
                    sub = load_stock_data(code, conn)
                    if sub is None: continue
                    _, _, m5_, m10_, m20_, my_ = extract_features(sub)
                    if m5_:
                        cx5.extend(m5_); cx10.extend(m10_); cx20.extend(m20_); cy.extend(my_)
                if not cx5: continue
                X5 = torch.FloatTensor(np.array(cx5, dtype=np.float32).reshape(-1,5,4))
                X10 = torch.FloatTensor(np.array(cx10, dtype=np.float32).reshape(-1,10,4))
                X20 = torch.FloatTensor(np.array(cx20, dtype=np.float32).reshape(-1,20,4))
                Y = torch.LongTensor(np.array(cy, dtype=np.int8))
                dl = DataLoader(TensorDataset(X5, X10, X20, Y), 256, True)
                for x5, x10, x20, yb in dl:
                    opt.zero_grad()
                    loss = crit(net(x5.to(device), x10.to(device), x20.to(device)), yb.to(device))
                    loss.backward(); opt.step()
                    total_loss += loss.item(); n_batches += 1
                del X5, X10, X20, Y, cx5, cx10, cx20, cy
            if ep % 3 == 0:
                print(f'  Epoch {ep}: loss={total_loss/max(n_batches,1):.4f} ({time.time()-t0:.1f}s)', flush=True)

        print('  Validating...', flush=True)
        net.eval()
        all_preds, all_labels = [], []
        for cs in range(0, len(mstnn_codes), CHUNK_M):
            for code in mstnn_codes[cs:cs+CHUNK_M]:
                sub = load_stock_data(code, conn)
                if sub is None: continue
                _, _, m5_, m10_, m20_, my_ = extract_features(sub)
                if not m5_: continue
                with torch.no_grad():
                    p = torch.softmax(net(
                        torch.FloatTensor(np.array(m5_, dtype=np.float32).reshape(-1,5,4)).to(device),
                        torch.FloatTensor(np.array(m10_, dtype=np.float32).reshape(-1,10,4)).to(device),
                        torch.FloatTensor(np.array(m20_, dtype=np.float32).reshape(-1,20,4)).to(device)), 1)[:,1].cpu().numpy()
                all_preds.extend(p); all_labels.extend(my_)
        auc_mstnn = roc_auc_score(all_labels, all_preds)
        print(f'MSTNN: AUC={auc_mstnn:.4f} ({time.time()-t0:.1f}s)', flush=True)
        torch.save(net.state_dict(), str(MODEL_DIR / 'mstnn_model.pth'))

        print('  Saving MSTNN predictions...', flush=True)
        for cs in range(0, len(mstnn_codes), CHUNK_M):
            for code in mstnn_codes[cs:cs+CHUNK_M]:
                sub = load_stock_data(code, conn)
                if sub is None: continue
                c = sub['close'].values.astype(np.float64)
                v = sub['volume'].values.astype(np.float64)
                h = sub['high'].values.astype(np.float64)
                l = sub['low'].values.astype(np.float64)
                pct = np.diff(c)/np.maximum(c[:-1],0.01)*100; pct = np.insert(pct,0,0)
                vr = v/np.maximum(np.convolve(v,np.ones(5)/5,mode='same'),1)
                vol = (h-l)/np.maximum(c,0.01)*100
                vchg = np.diff(v)/np.maximum(v[:-1],1)*100; vchg = np.insert(vchg,0,0)
                fa = np.nan_to_num(np.column_stack([pct,vr,vol,vchg]), nan=0.0, posinf=5.0, neginf=-5.0)
                f = fa[-20:].copy()
                for ch in range(4):
                    col = f[:,ch]; mn, sd = np.mean(col), np.std(col)
                    f[:,ch] = (col-mn)/sd if sd>1e-6 else col-mn
                net.eval()
                with torch.no_grad():
                    p = torch.softmax(net(
                        torch.FloatTensor(f[-5:].reshape(1,5,4)).to(device),
                        torch.FloatTensor(f[-10:].reshape(1,10,4)).to(device),
                        torch.FloatTensor(f.reshape(1,20,4)).to(device)), 1)[0,1].item()
                mstnn_probs[code] = float(p)
            if cs % 200 == 0:
                print(f'  MSTNN pred {cs+CHUNK_M}/{len(mstnn_codes)} ({time.time()-t0:.1f}s)', flush=True)
        with open(WORK_DIR/'scripts'/'mstnn_latest_prob.pkl', 'wb') as f:
            pickle.dump(mstnn_probs, f)
        print(f'MSTNN: {len(mstnn_probs)} stocks', flush=True)
    except Exception as e:
        print(f'MSTNN failed: {e}', flush=True)

conn.close()

# ─── 模型注册 ──────────────────────────────────────────────────────
print(f'\n{"="*60}', flush=True)
registry = {
    'production': 'lgbm_unified.pkl',
    'models': {
        'lgbm_unified.pkl': {
            'type': 'LGBMClassifier',
            'features': model.n_features_in_,
            'feature_names': FEAT_NAMES,
            'trees': model.n_estimators_,
            'auc': round(float(auc_lgbm), 4),
            'trained_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'samples': n_samples,
            'stocks': len(lgbm_probs),
            'quick': args.quick,
        }
    },
    'version': 4,
}
# 保留上一个版本
if REGISTRY_PATH.exists():
    try:
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            old_reg = json.load(f)
        old_id = old_reg.get('production', '')
        if old_id and old_id in old_reg.get('models', {}):
            old_model = old_reg['models'][old_id]
            old_model['retired_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            registry['models'][f'prev_{old_id}'] = old_model
    except:
        pass
with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)
print(f'Registry saved: {REGISTRY_PATH}', flush=True)

# ─── 清理死模型 ────────────────────────────────────────────────────
for f in glob.glob(str(MODEL_DIR / '*.*')):
    name = os.path.basename(f)
    if name not in KEEP:
        try:
            os.remove(f)
            print(f'Removed dead model: {name}', flush=True)
        except:
            pass

# ─── 输出摘要 ──────────────────────────────────────────────────────
print(f'\n{"="*60}', flush=True)
print(f'Done! ({time.time()-t0:.1f}s)', flush=True)
print(f'LightGBM: {len(lgbm_probs)} stocks, AUC={auc_lgbm:.4f}, probs mean={np.mean(vals):.4f}', flush=True)
if auc_mstnn:
    print(f'MSTNN: {len(mstnn_probs)} stocks, AUC={auc_mstnn:.4f}', flush=True)