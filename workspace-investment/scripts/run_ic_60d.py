# -*- coding: utf-8 -*-
"""IC滚动60天计算 - 优化版，带进度和超时"""
import sys, os, sqlite3, time, json
from datetime import datetime
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
DB_PATH = 'F:/market_data.db'
STORE_PATH = os.path.join(WORK_DIR, 'data', 'factors.db')

print(f"{'='*60}")
print(f"  IC滚动60天计算 @ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"{'='*60}")

total_start = time.time()

# Connect to DB
conn = sqlite3.connect(DB_PATH)

# Get target date (latest with T+1 data)
max_date = conn.execute("SELECT MAX(date) FROM daily_k").fetchone()[0]
prev_date = conn.execute(
    "SELECT MAX(date) FROM daily_k WHERE date < ?",
    (max_date,)
).fetchone()[0]
print(f"目标日期: {prev_date}, 数据截止: {max_date}")

# Get trading dates
dates_row = conn.execute(
    "SELECT DISTINCT date FROM daily_k WHERE date <= ? ORDER BY date DESC LIMIT 70",
    (prev_date,)
).fetchall()
dates = sorted([r[0] for r in dates_row])
print(f"交易日数: {len(dates)} (从 {dates[0]} 到 {dates[-1]})")

# Load factor calculator functions (cached)
print("\n加载因子计算器...")
FACTOR_DF_MAP = {
    'ma_5': ('close',), 'ma_10': ('close',), 'ma_20': ('close',), 'ma_60': ('close',),
    'rsi_14': ('close',), 'vol_ratio': ('volume',), 'pct_chg_1d': ('close',),
    'pct_chg_5d': ('close',), 'pct_chg_10d': ('close',), 'atr_14': ('high', 'low', 'close'),
    'obv': ('close', 'volume'), 'wr_14': ('close', 'high', 'low'), 'cci_20': ('close', 'high', 'low'),
    'vwap_5': ('close', 'volume'), 'volatility_20': ('close',), 'macd_bar': ('close',),
    'macd_cross': ('close',), 'macd_second_peak': ('close',), 'acceleration': ('close',),
    'breakout_strength': ('close', 'high'), 'avg_cost': ('close', 'volume'),
    'profit_ratio': ('close', 'volume'), 'concentration': ('close', 'volume'),
}
FACTOR_NAMES = list(FACTOR_DF_MAP.keys())
print(f"因子数: {len(FACTOR_NAMES)}")

# Check existing IC data
if os.path.exists(STORE_PATH):
    store_conn = sqlite3.connect(STORE_PATH)
    existing_store = store_conn.execute("SELECT DISTINCT date FROM ic_history ORDER BY date").fetchall()
    store_conn.close()
else:
    existing_store = []
print(f"已有IC数据: {len(existing_store)} 天")

# Compute IC for each date
total_records = 0
batch_size = 100

for date_idx, date in enumerate(dates):
    elapsed = time.time() - total_start
    print(f"\n[{date_idx+1}/{len(dates)}] {date} (耗时 {elapsed:.0f}s)...")
    
    # Get codes
    codes_row = conn.execute(
        "SELECT code FROM daily_k WHERE date = ? AND code NOT LIKE 'bj.%' AND close > 0 AND volume > 0",
        (date,)
    ).fetchall()
    codes = [r[0] for r in codes_row]
    
    # Get forward returns
    next_rows = conn.execute(
        "SELECT date, COUNT(*) FROM daily_k WHERE date > ? GROUP BY date HAVING COUNT(*) > 100 ORDER BY date ASC LIMIT 1",
        (date,)
    ).fetchall()
    if not next_rows:
        print(f"  无次日数据，跳过")
        continue
    next_date = next_rows[0][0]
    
    fr_rows = conn.execute(
        "SELECT a.code, (a.close - b.close) / b.close AS ret FROM daily_k a INNER JOIN daily_k b ON a.code = b.code AND b.date = ? WHERE a.date = ? AND a.code NOT LIKE 'bj.%' AND b.close > 0 AND a.close > 0",
        (next_date, date)
    ).fetchall()
    forward_rets = {r[0]: float(r[1]) for r in fr_rows}
    
    if len(forward_rets) < 50:
        print(f"  T+1数据不足 ({len(forward_rets)})，跳过")
        continue
    
    # Check if already computed
    store_conn = sqlite3.connect(STORE_PATH)
    existing_check = store_conn.execute(
        "SELECT COUNT(*) FROM ic_history WHERE date = ?", (date,)
    ).fetchone()[0]
    store_conn.close()
    
    if existing_check > 0:
        print(f"  已存在 {existing_check} 条记录，跳过")
        continue
    
    # Compute factor values in batches
    factor_values = {}
    valid_codes = list(forward_rets.keys())
    
    for i in range(0, len(valid_codes), batch_size):
        batch = valid_codes[i:i+batch_size]
        placeholders = ','.join(['?' for _ in batch])
        
        for code in batch:
            rows = conn.execute(
                "SELECT date, close, high, low, volume FROM daily_k WHERE code = ? AND date >= ? ORDER BY date ASC",
                (code, (datetime.strptime(date, '%Y-%m-%d') - __import__('datetime').timedelta(days=120)).strftime('%Y-%m-%d'))
            ).fetchall()
            if len(rows) >= 20:
                import pandas as pd
                df = pd.DataFrame(rows, columns=['date', 'close', 'high', 'low', 'volume'])
                factor_values[code] = df
        
        if (i // batch_size) % 5 == 0:
            print(f"  进度: {min(i+batch_size, len(valid_codes))}/{len(valid_codes)}")
    
    # Compute factors for each stock
    import numpy as np
    from scipy.stats import spearmanr
    
    all_factor_results = {}
    for code, df in factor_values.items():
        all_factor_results[code] = {}
        for fn in FACTOR_NAMES:
            try:
                cols = FACTOR_DF_MAP[fn]
                close = df['close'].astype(float)
                volume = df['volume'].astype(float)
                high = df['high'].astype(float)
                low = df['low'].astype(float)
                
                if fn == 'ma_5':
                    val = close / close.rolling(5).mean() - 1
                elif fn == 'ma_10':
                    val = close / close.rolling(10).mean() - 1
                elif fn == 'ma_20':
                    val = close / close.rolling(20).mean() - 1
                elif fn == 'ma_60':
                    val = close / close.rolling(60).mean() - 1
                elif fn == 'rsi_14':
                    delta = close.diff()
                    gain = delta.where(delta > 0, 0).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rs = gain / loss
                    val = 100 - (100 / (1 + rs))
                elif fn == 'vol_ratio':
                    val = volume / volume.rolling(20).mean()
                elif fn == 'pct_chg_1d':
                    val = close.pct_change(1)
                elif fn == 'pct_chg_5d':
                    val = close.pct_change(5)
                elif fn == 'pct_chg_10d':
                    val = close.pct_change(10)
                elif fn == 'atr_14':
                    tr1 = high - low
                    tr2 = abs(high - close.shift(1))
                    tr3 = abs(low - close.shift(1))
                    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                    val = tr.rolling(14).mean()
                elif fn == 'obv':
                    obv = (np.sign(close.diff()) * volume).cumsum()
                    val = obv / obv.abs().max() if obv.abs().max() > 0 else obv
                elif fn == 'wr_14':
                    tr = high - low
                    rh = high - high.shift(1)
                    rl = low.shift(1) - low
                    tr = tr.combine(pd.Series({'close': close}), lambda x, y: max(x, y, 0))
                    val = -100 * (tr / (high - low).rolling(14).sum())
                elif fn == 'cci_20':
                    tp = (high + low + close) / 3
                    mad = tp.rolling(20).apply(lambda x: abs(x - x.mean()).mean())
                    val = (tp - tp.rolling(20).mean()) / (0.015 * mad)
                elif fn == 'vwap_5':
                    vwap = (close * volume).rolling(5).sum() / volume.rolling(5).sum()
                    val = (close - vwap) / vwap
                elif fn == 'volatility_20':
                    val = close.pct_change().rolling(20).std()
                elif fn == 'macd_bar':
                    ema12 = close.ewm(span=12, adjust=False).mean()
                    ema26 = close.ewm(span=26, adjust=False).mean()
                    dif = ema12 - ema26
                    dea = dif.ewm(span=9, adjust=False).mean()
                    val = 2 * (dif - dea)
                elif fn == 'macd_cross':
                    ema12 = close.ewm(span=12, adjust=False).mean()
                    ema26 = close.ewm(span=26, adjust=False).mean()
                    dif = ema12 - ema26
                    dea = dif.ewm(span=9, adjust=False).mean()
                    cross = (dif.shift(1) - dea.shift(1)) * (dif - dea)
                    val = cross
                elif fn == 'macd_second_peak':
                    ema12 = close.ewm(span=12, adjust=False).mean()
                    ema26 = close.ewm(span=26, adjust=False).mean()
                    dif = ema12 - ema26
                    val = dif.diff().diff()
                elif fn == 'acceleration':
                    returns = close.pct_change()
                    val = (returns.rolling(5).mean() - returns.rolling(20).mean())
                elif fn == 'breakout_strength':
                    max_high_60 = high.rolling(60).max()
                    val = (close - max_high_60.shift(1)) / max_high_60.shift(1)
                elif fn == 'avg_cost':
                    avg = (close * volume).sum() / volume.sum() if volume.sum() > 0 else np.nan
                    val = (close.iloc[-1] - avg) / avg if not np.isnan(avg) else np.nan
                elif fn == 'profit_ratio':
                    ma20 = close.rolling(20).mean().iloc[-1]
                    ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else np.nan
                    ratio = 0.0
                    if not np.isnan(ma20): ratio += 0.5 * (1 if close.iloc[-1] > ma20 else 0)
                    if not np.isnan(ma60): ratio += 0.5 * (1 if close.iloc[-1] > ma60 else 0)
                    val = ratio
                elif fn == 'concentration':
                    total_vol = volume.sum()
                    if total_vol <= 0:
                        val = np.nan
                    else:
                        hist_vol = volume.tail(20).sum() if len(volume) >= 20 else volume.sum()
                        val = hist_vol / total_vol
                else:
                    val = df[cols[-1]].astype(float)
                
                if isinstance(val, pd.Series):
                    val = val.iloc[-1]
                if not np.isnan(val) and np.isfinite(val):
                    all_factor_results[code][fn] = float(val)
            except Exception:
                pass
    
    # Compute IC for each factor
    records = []
    all_factors_in_date = set()
    for fv in all_factor_results.values():
        all_factors_in_date.update(fv.keys())
    
    for factor_name in sorted(all_factors_in_date):
        factor_vals = []
        rets = []
        for code, fv in all_factor_results.items():
            if factor_name in fv and code in forward_rets:
                factor_vals.append(fv[factor_name])
                rets.append(forward_rets[code])
        
        if len(factor_vals) < 30:
            continue
        
        ic, p_value = spearmanr(factor_vals, rets)
        records.append({
            'date': date,
            'factor_name': factor_name,
            'ic': float(ic),
            'p_value': float(p_value) if not np.isnan(p_value) else None,
            'n_stocks': len(factor_vals),
        })
        total_records += 1
    
    # Save to factors.db
    if records:
        store_conn = sqlite3.connect(STORE_PATH)
        for record in records:
            store_conn.execute(
                "DELETE FROM ic_history WHERE date = ? AND factor_name = ?",
                (record['date'], record['factor_name'])
            )
        for record in records:
            store_conn.execute(
                "INSERT INTO ic_history (date, factor_name, ic, p_value, n_stocks) VALUES (?, ?, ?, ?, ?)",
                (record['date'], record['factor_name'], record['ic'], record['p_value'], record['n_stocks'])
            )
        store_conn.commit()
        store_conn.close()
        print(f"  保存 {len(records)} 条IC记录")
    
    # Update factor status every 5 dates
    if (date_idx + 1) % 5 == 0:
        store_conn = sqlite3.connect(STORE_PATH)
        rows = store_conn.execute("SELECT factor_name, ic FROM ic_history ORDER BY date DESC").fetchall()
        factor_stats = {}
        for fn, ic in rows:
            if fn not in factor_stats:
                factor_stats[fn] = []
            factor_stats[fn].append(ic)
        
        for fn, ics in factor_stats.items():
            ics_window = ics[:20]
            mean_ic = float(np.mean(ics_window))
            std_ic = float(np.std(ics_window))
            ic_ir = mean_ic / std_ic if std_ic > 0 else 0.0
            positive_ratio = sum(1 for x in ics_window if x > 0) / len(ics_window)
            n_days = len(ics_window)
            status = 'active'
            if abs(mean_ic) < 0.02 and n_days >= 10:
                status = 'eliminated'
            
            store_conn.execute("""
                INSERT INTO factor_status (factor_name, category, mean_ic, ic_ir, positive_ratio, n_days, status, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(factor_name) DO UPDATE SET
                    mean_ic = excluded.mean_ic, ic_ir = excluded.ic_ir,
                    positive_ratio = excluded.positive_ratio, n_days = excluded.n_days,
                    status = excluded.status, last_updated = excluded.last_updated
            """, (fn, 'technical', mean_ic, ic_ir, positive_ratio, n_days, status, datetime.now().strftime('%Y-%m-%d')))
        store_conn.commit()
        store_conn.close()
        print(f"  因子状态已更新 ({len(factor_stats)} 个因子)")

conn.close()

# Final report
elapsed = time.time() - total_start
print(f"\n{'='*60}")
print(f"  完成！耗时 {elapsed:.0f}s")
print(f"  共计算 {total_records} 条IC记录")
print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}")
