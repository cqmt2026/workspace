# -*- coding: utf-8 -*-
"""
简化版MSTNN (Multi-Scale Temporal Neural Network)
==================================================
用3D卷积思想提取多尺度时序特征。

核心设计：
  1. 多尺度窗口：5天(短)、10天(中)、20天(长) 三个时间尺度
  2. 特征通道：涨跌幅、量比、波动率、成交额变化率
  3. 3D卷积变体：每个尺度独立1D卷积 → 拼接 → 全连接 → 输出
  4. 轻量化：仅2层卷积+2层全连接，参数<100K，防过拟合

数据流：
  DB日K线 → 多尺度切片 → 特征标准化 → 卷积 → 池化 → 拼接 → FC → 输出概率

依赖：pytorch, numpy, pandas, sqlite3

训练方法：
  python mstnn_model.py --train
  
预测（批量）：
  python mstnn_model.py --predict --date 2026-07-01
  
预测（单只）：
  python mstnn_model.py --single sz.000858
"""

import os
import sys
import io
import json
import pickle
import random
import numpy as np
import sqlite3
from datetime import datetime, date, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB = r'F:\market_data.db'
WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
MODEL_DIR = os.path.join(WORK_DIR, 'quant_ml', 'data', 'models')
OUT_DIR = os.path.join(WORK_DIR, 'out_data')
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[MSTNN] PyTorch未安装，请: pip install torch")


# ============================================================
# 特征工程：多尺度切片
# ============================================================

FEATURE_CHANNELS = 4  # 涨跌幅、量比、波动率、成交额变化率

def safe_float(v, default=0.0):
    try:
        f = float(v)
        return f if not np.isnan(f) and not np.isinf(f) else default
    except:
        return default

def build_mstnn_features(conn, code, max_date, window_sizes=[5, 10, 20]):
    """构建多尺度特征矩阵"""
    rows = conn.execute("""
        SELECT date, close, volume, high, low
        FROM daily_k
        WHERE code = ? AND date <= ?
        ORDER BY date DESC LIMIT 30
    """, (code, max_date)).fetchall()
    
    if len(rows) < max(window_sizes) + 2:
        return None
    
    rows = list(reversed(rows))
    
    closes = np.array([safe_float(r[1]) for r in rows], dtype=np.float64)
    volumes = np.array([safe_float(r[2]) for r in rows], dtype=np.float64)
    highs = np.array([safe_float(r[3]) for r in rows], dtype=np.float64)
    lows = np.array([safe_float(r[4]) for r in rows], dtype=np.float64)
    
    # 1. 涨跌幅 (%)
    pct_chg = np.diff(closes) / np.maximum(closes[:-1], 0.01) * 100
    pct_chg = np.insert(pct_chg, 0, 0)
    
    # 2. 量比
    vol_ma5 = np.convolve(volumes, np.ones(5)/5, mode='same')
    vol_ma5[:4] = np.mean(volumes[:5])
    vol_ratio = volumes / np.maximum(vol_ma5, 1)
    
    # 3. 波动率
    volatility = (highs - lows) / np.maximum(closes, 0.01) * 100
    
    # 4. 成交额变化率
    vol_chg = np.diff(volumes) / np.maximum(volumes[:-1], 1) * 100
    vol_chg = np.insert(vol_chg, 0, 0)
    
    features = np.column_stack([pct_chg, vol_ratio, volatility, vol_chg])
    features = np.nan_to_num(features, nan=0.0, posinf=5.0, neginf=-5.0)
    
    result = {}
    for w in window_sizes:
        if len(features) >= w:
            window_data = features[-w:].copy()
            for c in range(FEATURE_CHANNELS):
                col = window_data[:, c]
                mean, std = np.mean(col), np.std(col)
                if std > 1e-6:
                    window_data[:, c] = (col - mean) / std
                else:
                    window_data[:, c] = col - mean
            result[w] = window_data
        else:
            return None
    return result


# ============================================================
# 数据集构建（随机历史采样，确保有T+5标签）
# ============================================================

def prepare_dataset(date_str=None, min_samples=5000, sample_size=2000):
    """从DB构建训练数据集，随机历史日期采样"""
    if date_str is None:
        date_str = date.today().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB)
    
    # 获取非ST、非北交所股票
    all_codes = [r[0] for r in conn.execute("""
        SELECT DISTINCT code FROM daily_k 
        WHERE code NOT LIKE 'bj.%%' AND code NOT LIKE 'sh.8%%'
    """).fetchall()]
    st_codes = set(r[0] for r in conn.execute("SELECT code FROM stock_st_status WHERE is_st=1").fetchall())
    all_codes = [c for c in all_codes if c not in st_codes]
    
    # 可用历史日期（去掉最后10天，需要T+5有数据）
    all_dates = [r[0] for r in conn.execute("""
        SELECT DISTINCT date FROM daily_k WHERE date <= ? ORDER BY date
    """, (date_str,)).fetchall()]
    
    if len(all_dates) < 20:
        conn.close()
        print(f"[MSTNN] 数据不足，仅{len(all_dates)}个交易日")
        return None
    
    train_dates = all_dates[-(min(len(all_dates), 200)):-10]
    
    random.seed(42)
    np.random.seed(42)
    
    if len(all_codes) > sample_size:
        codes_sample = random.sample(all_codes, sample_size)
    else:
        codes_sample = all_codes
    
    samples_5, samples_10, samples_20, labels, codes_used = [], [], [], [], []
    total = len(codes_sample)
    collected = 0
    skipped = 0
    
    print(f"[MSTNN] 构建数据集，目标:{date_str}, 采样股票:{total}, 交易日:{len(train_dates)}")
    
    for i, code in enumerate(codes_sample):
        train_date = random.choice(train_dates)
        features = build_mstnn_features(conn, code, train_date)
        if features is None:
            skipped += 1
            continue
        
        future_rows = conn.execute("""
            SELECT close FROM daily_k WHERE code = ? AND date > ? ORDER BY date LIMIT 5
        """, (code, train_date)).fetchall()
        
        if len(future_rows) < 5:
            skipped += 1
            continue
        
        try:
            future_close = safe_float(future_rows[-1][0])
        except:
            skipped += 1
            continue
        
        curr = conn.execute("SELECT close FROM daily_k WHERE code = ? AND date = ?", (code, train_date)).fetchone()
        if curr is None:
            skipped += 1
            continue
        current_close = safe_float(curr[0])
        if current_close <= 0:
            skipped += 1
            continue
        
        label = 1 if future_close > current_close else 0
        
        samples_5.append(features[5].flatten())
        samples_10.append(features[10].flatten())
        samples_20.append(features[20].flatten())
        labels.append(label)
        codes_used.append(code)
        collected += 1
        
        if (i + 1) % 500 == 0:
            print(f"  [MSTNN] 已处理 {i+1}/{total}，收集 {collected} 样本，跳过 {skipped}")
    
    conn.close()
    print(f"[MSTNN] 数据集完成: {collected} 样本, {skipped} 跳过")
    
    if collected < min_samples:
        print(f"[MSTNN] 样本不足 {min_samples}，当前 {collected}")
    
    if collected == 0:
        return None
    
    return {
        'X_5': np.array(samples_5),
        'X_10': np.array(samples_10),
        'X_20': np.array(samples_20),
        'y': np.array(labels),
        'codes': codes_used,
    }


# ============================================================
# MSTNN模型定义
# ============================================================

class MSTNN(nn.Module):
    """简化版MSTNN - 3个独立1D卷积支路"""
    
    def __init__(self, channels=4, dropout=0.3):
        super().__init__()
        self.conv_5 = nn.Sequential(
            nn.Conv1d(channels, 16, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool1d(kernel_size=2), nn.Dropout(dropout),
            nn.Conv1d(16, 32, kernel_size=3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.conv_10 = nn.Sequential(
            nn.Conv1d(channels, 16, kernel_size=5, padding=2), nn.ReLU(),
            nn.MaxPool1d(kernel_size=2), nn.Dropout(dropout),
            nn.Conv1d(16, 32, kernel_size=5, padding=2), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.conv_20 = nn.Sequential(
            nn.Conv1d(channels, 16, kernel_size=7, padding=3), nn.ReLU(),
            nn.MaxPool1d(kernel_size=2), nn.Dropout(dropout),
            nn.Conv1d(16, 32, kernel_size=7, padding=3), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.fc = nn.Sequential(
            nn.Linear(32 * 3, 64), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(64, 2),
        )
    
    def forward(self, x_5, x_10, x_20):
        x_5 = x_5.permute(0, 2, 1)
        x_10 = x_10.permute(0, 2, 1)
        x_20 = x_20.permute(0, 2, 1)
        f5 = self.conv_5(x_5).squeeze(-1)
        f10 = self.conv_10(x_10).squeeze(-1)
        f20 = self.conv_20(x_20).squeeze(-1)
        combined = torch.cat([f5, f10, f20], dim=1)
        return self.fc(combined)


class MSTNNDataset(Dataset):
    def __init__(self, X_5, X_10, X_20, y):
        self.X_5 = torch.FloatTensor(X_5.reshape(-1, 5, FEATURE_CHANNELS))
        self.X_10 = torch.FloatTensor(X_10.reshape(-1, 10, FEATURE_CHANNELS))
        self.X_20 = torch.FloatTensor(X_20.reshape(-1, 20, FEATURE_CHANNELS))
        self.y = torch.LongTensor(y)
    
    def __len__(self):
        return len(self.y)
    
    def __getitem__(self, idx):
        return self.X_5[idx], self.X_10[idx], self.X_20[idx], self.y[idx]


# ============================================================
# 训练
# ============================================================

def train_mstnn(data, epochs=50, batch_size=256, lr=0.001):
    """训练MSTNN模型"""
    if not TORCH_AVAILABLE:
        print("[MSTNN] PyTorch不可用，跳过训练")
        return None
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[MSTNN] 使用设备: {device}")
    
    X_5, X_10, X_20, y = data['X_5'], data['X_10'], data['X_20'], data['y']
    
    split = int(len(y) * 0.8)
    indices = np.random.permutation(len(y))
    train_idx, val_idx = indices[:split], indices[split:]
    
    train_dataset = MSTNNDataset(X_5[train_idx], X_10[train_idx], X_20[train_idx], y[train_idx])
    val_dataset = MSTNNDataset(X_5[val_idx], X_10[val_idx], X_20[val_idx], y[val_idx])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    model = MSTNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
    
    print(f"[MSTNN] 训练: {len(train_dataset)} 训练, {len(val_dataset)} 验证, {epochs} 轮")
    
    best_val_acc = 0.0
    best_model_state = None
    
    for epoch in range(epochs):
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0
        for x5, x10, x20, yb in train_loader:
            x5, x10, x20, yb = x5.to(device), x10.to(device), x20.to(device), yb.to(device)
            optimizer.zero_grad()
            outputs = model(x5, x10, x20)
            loss = criterion(outputs, yb)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            train_total += yb.size(0)
            train_correct += (predicted == yb).sum().item()
        train_acc = train_correct / train_total
        
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        all_probs, all_labels = [], []
        with torch.no_grad():
            for x5, x10, x20, yb in val_loader:
                x5, x10, x20, yb = x5.to(device), x10.to(device), x20.to(device), yb.to(device)
                outputs = model(x5, x10, x20)
                loss = criterion(outputs, yb)
                val_loss += loss.item()
                probs = torch.softmax(outputs, 1)[:, 1].cpu().numpy()
                all_probs.extend(probs)
                all_labels.extend(yb.cpu().numpy())
                _, predicted = torch.max(outputs, 1)
                val_total += yb.size(0)
                val_correct += (predicted == yb).sum().item()
        val_acc = val_correct / val_total
        
        try:
            from sklearn.metrics import roc_auc_score
            val_auc = roc_auc_score(all_labels, all_probs)
        except:
            val_auc = 0.0
        
        scheduler.step(val_loss / len(val_loader))
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"  Epoch {epoch+1:3d}/{epochs} | TrL:{train_loss/len(train_loader):.4f} TrA:{train_acc:.4f} | VaL:{val_loss/len(val_loader):.4f} VaA:{val_acc:.4f} AUC:{val_auc:.4f}")
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    
    if best_model_state:
        model.load_state_dict(best_model_state)
    
    model_path = os.path.join(MODEL_DIR, 'mstnn_model.pth')
    torch.save({'model_state': best_model_state or model.state_dict(), 'val_acc': best_val_acc, 'config': {'channels': FEATURE_CHANNELS, 'epochs': epochs}}, model_path)
    print(f"[MSTNN] 模型保存: {model_path} (val_acc: {best_val_acc:.4f})")
    
    # 保存概率
    prob_path = os.path.join(WORK_DIR, 'scripts', 'mstnn_latest_prob.pkl')
    model.eval()
    all_probs = []
    with torch.no_grad():
        dataset = MSTNNDataset(X_5, X_10, X_20, y)
        loader = DataLoader(dataset, batch_size=batch_size)
        for x5, x10, x20, _ in loader:
            x5, x10, x20 = x5.to(device), x10.to(device), x20.to(device)
            outputs = model(x5, x10, x20)
            probs = torch.softmax(outputs, 1)[:, 1].cpu().numpy()
            all_probs.extend(probs)
    prob_dict = dict(zip(data['codes'], all_probs))
    with open(prob_path, 'wb') as f:
        pickle.dump(prob_dict, f)
    print(f"[MSTNN] 概率保存: {prob_path} ({len(prob_dict)}只)")
    
    return model, best_val_acc


# ============================================================
# 预测
# ============================================================

def predict_single(model, code, date_str=None):
    if date_str is None:
        date_str = date.today().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB)
    features = build_mstnn_features(conn, code, date_str)
    conn.close()
    if features is None:
        return 0.5
    device = next(model.parameters()).device
    with torch.no_grad():
        x5 = torch.FloatTensor(features[5].flatten().reshape(1, -1, FEATURE_CHANNELS)).to(device)
        x10 = torch.FloatTensor(features[10].flatten().reshape(1, -1, FEATURE_CHANNELS)).to(device)
        x20 = torch.FloatTensor(features[20].flatten().reshape(1, -1, FEATURE_CHANNELS)).to(device)
        outputs = model(x5, x10, x20)
        return torch.softmax(outputs, 1)[0, 1].item()


class MSTNNPredictor:
    def __init__(self):
        self.model = None
        self.model_path = os.path.join(MODEL_DIR, 'mstnn_model.pth')
        self.loaded = False
    
    def load(self):
        if not TORCH_AVAILABLE or not os.path.exists(self.model_path):
            return False
        try:
            checkpoint = torch.load(self.model_path, map_location='cpu')
            self.model = MSTNN()
            self.model.load_state_dict(checkpoint['model_state'])
            self.model.eval()
            self.loaded = True
            print(f"[MSTNN] 模型加载成功 (val_acc: {checkpoint.get('val_acc', '?'):.4f})")
            return True
        except Exception as e:
            print(f"[MSTNN] 模型加载失败: {e}")
            return False
    
    def predict_batch(self, codes, date_str=None):
        if not self.loaded:
            return {c: 0.5 for c in codes}
        if date_str is None:
            date_str = date.today().strftime('%Y-%m-%d')
        conn = sqlite3.connect(DB)
        results = {}
        device = next(self.model.parameters()).device
        for code in codes:
            features = build_mstnn_features(conn, code, date_str)
            if features is None:
                results[code] = 0.5
                continue
            with torch.no_grad():
                x5 = torch.FloatTensor(features[5].flatten().reshape(1, -1, FEATURE_CHANNELS)).to(device)
                x10 = torch.FloatTensor(features[10].flatten().reshape(1, -1, FEATURE_CHANNELS)).to(device)
                x20 = torch.FloatTensor(features[20].flatten().reshape(1, -1, FEATURE_CHANNELS)).to(device)
                outputs = self.model(x5, x10, x20)
                results[code] = torch.softmax(outputs, 1)[0, 1].item()
        conn.close()
        return results


# ============================================================
# 主入口
# ============================================================

if __name__ == '__main__':
    if '--train' in sys.argv:
        print("=" * 60)
        print("MSTNN 多尺度时序网络 - 训练")
        print("=" * 60)
        data = prepare_dataset()
        if data:
            print(f"数据集: X5:{data['X_5'].shape}, X10:{data['X_10'].shape}, X20:{data['X_20'].shape}, y:{data['y'].shape}")
            print(f"正样本率: {data['y'].mean():.2%}")
            model, val_acc = train_mstnn(data, epochs=50)
            if model:
                print(f"\nMSTNN训练完成，验证集准确率: {val_acc:.4f}")
    
    elif '--predict' in sys.argv:
        print("=" * 60)
        print("MSTNN 批量预测")
        print("=" * 60)
        date_str = None
        for i, arg in enumerate(sys.argv):
            if arg == '--date' and i + 1 < len(sys.argv):
                date_str = sys.argv[i + 1]
        if date_str is None:
            date_str = date.today().strftime('%Y-%m-%d')
        
        predictor = MSTNNPredictor()
        if not predictor.load():
            print("模型加载失败，请先训练")
            sys.exit(1)
        
        conn = sqlite3.connect(DB)
        codes = [r[0] for r in conn.execute("""
            SELECT DISTINCT code FROM daily_k WHERE date = ? AND code NOT LIKE 'bj.%%' AND code NOT LIKE 'sh.8%%'
        """, (date_str,)).fetchall()]
        st_codes = set(r[0] for r in conn.execute("SELECT code FROM stock_st_status WHERE is_st=1").fetchall())
        codes = [c for c in codes if c not in st_codes]
        conn.close()
        
        print(f"预测: {date_str}, 股票: {len(codes)}")
        probs = predictor.predict_batch(codes, date_str)
        sorted_probs = sorted(probs.items(), key=lambda x: -x[1])
        print(f"\nTOP20:")
        for i, (code, prob) in enumerate(sorted_probs[:20], 1):
            print(f"  {i:2d}. {code:<14} {prob:.4f}")
        
        prob_path = os.path.join(WORK_DIR, 'scripts', 'mstnn_latest_prob.pkl')
        with open(prob_path, 'wb') as f:
            pickle.dump(probs, f)
        print(f"概率保存: {prob_path} ({len(probs)}只)")
    
    elif '--single' in sys.argv:
        idx = sys.argv.index('--single')
        code = sys.argv[idx + 1]
        print(f"MSTNN 预测 {code}:")
        predictor = MSTNNPredictor()
        if predictor.load():
            prob = predict_single(predictor.model, code)
            print(f"  T+5上涨概率: {prob:.4f}")
    
    else:
        print("用法:")
        print("  python mstnn_model.py --train             # 训练模型")
        print("  python mstnn_model.py --predict --date D  # 批量预测")
        print("  python mstnn_model.py --single CODE       # 单只预测")
        print("  需安装 PyTorch (pip install torch)")