# -*- coding: utf-8 -*-
"""
快速IC滚动计算 - 仅计算缺失日期的IC
优化版：批量查询 + 并行因子计算
"""
import io, sys, os, json, sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.stats import spearmanr

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORK_DIR)

DB_PATH = r'F:/market_data.db'
FACTORS_DB = os.path.join(WORK_DIR, 'data/factors.db')

# Factor definitions (same as daily_ic_compute.py)
FACTOR_NAMES = [
    'ma_5', 'ma_10', 'ma_20', 'ma_60', 'rsi_14', 'vol_ratio',
    'pct_chg_1d', 'pct_chg_5d', 'pct_chg_10d', 'atr_14', 'obv',
    'wr_14', 'cci_20', 'vwap_5', 'volatility_20',
    'macd_bar', 'macd_cross', 'macd_second_peak',
    'acceleration', 'breakout_strength',
    'avg_cost', 'profit_ratio', 'concentration',
]

def load_klines(conn, codes, start_date, end_date):
    """批量加载K线数据"""
    placeholders = ','.join(['?' for _ in codes])
    query = f"""
        SELECT code, date, close, high, low, volume
        FROM daily_k
        WHERE code IN ({placeholders})
        AND date >= ? AND date <= ?
        ORDER BY code, date
    """
    params = codes + [start_date, end_date]
    df = pd.read_sql_query(query, conn, params=params)
    return df

def compute_factors_batch(df_grouped):
    """批量计算所有因子"""
    results = {}
    for code, df in df_grouped:
        if len(df) < 20:
            continue
        close = pd.to_numeric(df['close'], errors='coerce')
        high = pd.to_numeric(df['high'], errors='coerce')
        low = pd.to_numeric(df['low'], errors='coerce')
        volume = pd.to_numeric(df['volume'], errors='coerce').fillna(0)

        code_factors = {}

        # MA factors
        for period in [5, 10, 20, 60]:
            key = f'ma_{period}'
            ma = close.rolling(period).mean()
            code_factors[key] = float((close / ma - 1).iloc[-1]) if not pd.isna(ma.iloc[-1]) else np.nan

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        code_factors['rsi_14'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else np.nan

        # Volume ratio
        vol_ma = volume.rolling(20).mean()
        code_factors['vol_ratio'] = float((volume / vol_ma).iloc[-1]) if not pd.isna(vol_ma.iloc[-1]) else np.nan

        #_pct changes
        for period in [1, 5, 10]:
            key = f'pct_chg_{period}d'
            code_factors[key] = float(close.pct_change(period).iloc[-1]) if not pd.isna(close.pct_change(period).iloc[-1]) else np.nan

        # ATR
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        code_factors['atr_14'] = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else np.nan

        # OBV
        obv = (np.sign(close.diff()) * volume).cumsum()
        code_factors['obv'] = float((obv / obv.abs().max()).iloc[-1]) if obv.abs().max() > 0 else np.nan

        # VWAP
        vwap = (close * volume).rolling(5).sum() / volume.rolling(5).sum()
        code_factors['vwap_5'] = float(((close - vwap) / vwap).iloc[-1]) if not pd.isna(vwap.iloc[-1]) else np.nan

        # Volatility
        code_factors['volatility_20'] = float(close.pct_change().rolling(20).std().iloc[-1]) if not pd.isna(close.pct_change().rolling(20).std().iloc[-1]) else np.nan

        # MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        macd_bar = 2 * (dif - dea)
        macd_cross = (dif.shift(1) - dea.shift(1)) * (dif - dea)
        macd_second_peak = dif.diff().diff()
        code_factors['macd_bar'] = float(macd_bar.iloc[-1]) if not pd.isna(macd_bar.iloc[-1]) else np.nan
        code_factors['macd_cross'] = float(macd_cross.iloc[-1]) if not pd.isna(macd_cross.iloc[-1]) else np.nan
        code_factors['macd_second_peak'] = float(macd_second_peak.iloc[-1]) if not pd.isna(macd_second_peak.iloc[-1]) else np.nan

        # Acceleration
        returns = close.pct_change()
        accel = returns.rolling(5).mean() - returns.rolling(20).mean()
        code_factors['acceleration'] = float(accel.iloc[-1]) if not pd.isna(accel.iloc[-1]) else np.nan

        # Breakout strength
        max_high_60 = high.rolling(60).max()
        code_factors['breakout_strength'] = float(((close - max_high_60.shift(1)) / max_high_60.shift(1)).iloc[-1]) if not pd.isna(max_high_60.shift(1).iloc[-1]) else np.nan

        # Avg cost
        avg = (close * volume).sum() / volume.sum() if volume.sum() > 0 else np.nan
        code_factors['avg_cost'] = float((close.iloc[-1] - avg) / avg) if not pd.isna(avg) and avg != 0 else np.nan

        # Profit ratio
        price = close.iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else np.nan
        ratio = 0.0
        if not pd.isna(ma20):
            ratio += 0.5 * (1 if price > ma20 else 0)
        if not pd.isna(ma60):
            ratio += 0.5 * (1 if price > ma60 else 0)
        code_factors['profit_ratio'] = ratio

        # Concentration
        total_vol = volume.sum()
        if total_vol > 0:
            hist_vol = volume.tail(20).sum() if len(volume) >= 20 else volume.sum()
            code_factors['concentration'] = float(hist_vol / total_vol)
        else:
            code_factors['concentration'] = np.nan

        results[code] = code_factors

    return results

def main():
    print(f"="*60)
    print(f"  快速IC滚动计算 (仅补缺失日期)")
    print(f"="*60)

    conn = sqlite3.connect(DB_PATH)
    wconn = sqlite3.connect(FACTORS_DB)

    # Get all trading dates
    all_dates = [r[0] for r in conn.execute("SELECT DISTINCT date FROM daily_k ORDER BY date DESC")]
    print(f"总交易日数: {len(all_dates)}")

    # Get existing IC dates
    ic_dates = [r[0] for r in wconn.execute("SELECT DISTINCT date FROM ic_history ORDER BY date")]
    print(f"已有IC数据: {len(ic_dates)} 天 ({ic_dates[0]} ~ {ic_dates[-1]})")

    # Find missing dates in last 60 trading days
    last_60 = all_dates[:60]
    missing_dates = [d for d in last_60 if d not in ic_dates]
    print(f"缺失IC数据: {len(missing_dates)} 天")
    for d in missing_dates:
        print(f"  {d}")

    if not missing_dates:
        print("所有日期IC数据已完整!")
        conn.close()
        wconn.close()
        return

    # Process each missing date
    all_records = []
    for target_date in missing_dates:
        print(f"\n处理 {target_date}...")

        # Get codes for this date
        codes_row = conn.execute("""
            SELECT code FROM daily_k WHERE date = ?
            AND code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%%'
            AND code NOT LIKE 'sh.9%%' AND code NOT LIKE 'sh.4%%'
            AND code NOT LIKE 'sh.68%%'
            AND close > 0 AND volume > 0
        """, (target_date,)).fetchall()
        codes = [r[0] for r in codes_row]
        print(f"  股票数: {len(codes)}")

        if len(codes) < 100:
            print("  数据不足，跳过")
            continue

        # Get forward returns (T+1)
        next_date_row = conn.execute("""
            SELECT date, COUNT(*) as cnt FROM daily_k
            WHERE date > ? GROUP BY date HAVING cnt > 100
            ORDER BY date ASC LIMIT 1
        """, (target_date,)).fetchone()

        if not next_date_row:
            print("  无T+1数据，跳过")
            continue

        next_date = next_date_row[0]

        # Get forward returns
        fwd_rows = conn.execute("""
            SELECT a.code, (a.close - b.close) / b.close as ret
            FROM daily_k a
            INNER JOIN daily_k b ON a.code = b.code AND b.date = ?
            WHERE a.date = ?
            AND a.code NOT LIKE 'bj.%' AND a.code NOT LIKE 'sh.8%%'
            AND b.close > 0 AND a.close > 0
        """, (next_date, target_date)).fetchall()
        forward_rets = {r[0]: float(r[1]) for r in fwd_rows if r[1] is not None}
        print(f"  T+1配对: {len(forward_rets)} 只")

        if len(forward_rets) < 50:
            print("  T+1数据不足，跳过")
            continue

        # Get K-line data for factor computation
        start_date = (pd.Timestamp(target_date) - timedelta(days=120)).strftime('%Y-%m-%d')
        kline_df = load_klines(conn, list(forward_rets.keys()), start_date, target_date)

        if len(kline_df) == 0:
            print("  无K线数据，跳过")
            continue

        # Group by code
        df_grouped = kline_df.groupby('code')

        # Compute factors
        factor_results = compute_factors_batch(df_grouped)
        print(f"  因子计算完成: {len(factor_results)} 只")

        # Compute IC for each factor
        for factor_name in FACTOR_NAMES:
            factor_vals = []
            rets = []
            valid_codes = []

            for code, fv in factor_results.items():
                if factor_name in fv and code in forward_rets:
                    val = fv[factor_name]
                    if not np.isnan(val) and np.isfinite(val):
                        factor_vals.append(val)
                        rets.append(forward_rets[code])
                        valid_codes.append(code)

            if len(factor_vals) < 30:
                continue

            ic, p_value = spearmanr(factor_vals, rets)

            record = {
                'date': target_date,
                'factor_name': factor_name,
                'ic': float(ic),
                'p_value': float(p_value) if not np.isnan(p_value) else None,
                'n_stocks': len(factor_vals),
            }
            all_records.append(record)
            print(f"    {factor_name}: IC={ic:.4f}, p={p_value:.4f}")

    # Save to factors.db
    if all_records:
        wconn.execute("""
            CREATE TABLE IF NOT EXISTS ic_history (
                date TEXT, factor_name TEXT, ic REAL, p_value REAL, n_stocks INTEGER,
                PRIMARY KEY (date, factor_name)
            )
        """)

        for record in all_records:
            wconn.execute(
                "DELETE FROM ic_history WHERE date = ? AND factor_name = ?",
                (record['date'], record['factor_name'])
            )
            wconn.execute(
                """INSERT INTO ic_history (date, factor_name, ic, p_value, n_stocks)
                   VALUES (?, ?, ?, ?, ?)""",
                (record['date'], record['factor_name'], record['ic'],
                 record['p_value'], record['n_stocks'])
            )
        wconn.commit()
        print(f"\n保存 {len(all_records)} 条IC记录")

        # Generate report
        output_dir = os.path.join(WORK_DIR, 'out_data')
        os.makedirs(output_dir, exist_ok=True)
        latest_date = max(r['date'] for r in all_records)
        output_path = os.path.join(output_dir, f'ic_report_{latest_date}.json')

        # Read all IC data for summary
        all_ic = wconn.execute("SELECT date, factor_name, ic, p_value, n_stocks FROM ic_history").fetchall()
        all_records_full = [{'date': r[0], 'factor_name': r[1], 'ic': r[2], 'p_value': r[3], 'n_stocks': r[4]} for r in all_ic]

        report = {
            'date': latest_date,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_factors': len([r for r in all_records_full if r['date'] == latest_date]),
            'records': [r for r in all_records_full if r['date'] == latest_date],
            'summary': {
                'avg_ic': float(np.mean([r['ic'] for r in all_records_full if r['date'] == latest_date])),
                'max_ic': float(max([abs(r['ic']) for r in all_records_full if r['date'] == latest_date])),
                'min_ic': float(min([r['ic'] for r in all_records_full if r['date'] == latest_date])),
                'significant_count': sum(1 for r in all_records_full if r['date'] == latest_date and r['p_value'] is not None and r['p_value'] < 0.05),
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"报告已生成: {output_path}")

    # Update factor status
    print("\n更新因子状态...")
    wconn.execute('DROP TABLE IF EXISTS factor_status')
    wconn.execute("""
        CREATE TABLE factor_status (
            factor_name TEXT PRIMARY KEY,
            category TEXT,
            mean_ic REAL,
            ic_ir REAL,
            positive_ratio REAL,
            n_days INTEGER,
            status TEXT,
            last_updated TEXT
        )
    """)

    rows = wconn.execute("SELECT factor_name, ic, p_value FROM ic_history ORDER BY date DESC").fetchall()
    factor_stats = {}
    for factor_name, ic, p_value in rows:
        if factor_name not in factor_stats:
            factor_stats[factor_name] = {'ics': [], 'p_values': []}
        factor_stats[factor_name]['ics'].append(ic)
        if p_value is not None:
            factor_stats[factor_name]['p_values'].append(p_value)

    for factor_name, stats in factor_stats.items():
        ics = stats['ics'][:60]  # Use 60-day window
        p_values = stats['p_values']
        if not ics:
            continue
        mean_ic = float(np.mean(ics))
        abs_ics = [abs(x) for x in ics]
        ic_ir = mean_ic / float(np.std(ics)) if np.std(ics) > 0 else 0.0
        positive_ratio = sum(1 for x in ics if x > 0) / len(ics)
        n_days = len(ics)
        status = 'active'
        if abs(mean_ic) < 0.02 and p_values and np.mean(p_values) > 0.1:
            status = 'eliminated'
        wconn.execute("""
            INSERT INTO factor_status (factor_name, category, mean_ic, ic_ir, positive_ratio, n_days, status, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(factor_name) DO UPDATE SET
                mean_ic = excluded.mean_ic, ic_ir = excluded.ic_ir,
                positive_ratio = excluded.positive_ratio, n_days = excluded.n_days,
                status = excluded.status, last_updated = excluded.last_updated
        """, (factor_name, 'technical', mean_ic, ic_ir, positive_ratio, n_days, status, datetime.now().strftime('%Y-%m-%d')))

    wconn.commit()
    print(f"因子状态更新完成: {len(factor_stats)} 个因子")

    # Print summary
    print(f"\n完成! IC历史: {len([r for r in all_records if True])} 条新记录")
    print(f"  总IC记录数: {len(all_ic)}")
    print(f"  日期范围: {min(r[0] for r in all_ic)} ~ {max(r[0] for r in all_ic)}")

    conn.close()
    wconn.close()

if __name__ == '__main__':
    main()
