# -*- coding: utf-8 -*-
"""
快速IC滚动计算脚本 - 批量查询优化版
====================================
相比原版 daily_ic_compute.py，此版本：
1. 批量获取K线数据（一次JOIN查所有股票）
2. 减少数据库查询次数
3. 使用numpy向量化计算替代pandas逐行计算
4. 输出实时进度
"""
import sys
import os
import time
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.stats import spearmanr

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = 'F:/market_data.db'
STORE_DB = os.path.join(WORK_DIR, 'data', 'factors.db')

# ─── 因子计算器（向量化版本）───
def compute_technical_factors(df: pd.DataFrame) -> dict:
    """批量计算技术因子，返回{factor_name: value}"""
    close = df['close'].astype(float)
    high = df['high'].astype(float)
    low = df['low'].astype(float)
    volume = df['volume'].astype(float)
    results = {}

    # MA比率
    for period in (5, 10, 20, 60):
        key = f'ma_{period}'
        ma = close.rolling(period).mean()
        results[key] = (close / ma - 1).iloc[-1] if ma.iloc[-1] != 0 else np.nan

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    results['rsi_14'] = (100 - 100 / (1 + rs)).iloc[-1]

    # 涨跌幅
    for period in (1, 5, 10):
        key = f'pct_chg_{period}d'
        results[key] = close.pct_change(period).iloc[-1]

    # 量比
    results['vol_ratio'] = (volume / volume.rolling(20).mean()).iloc[-1]

    # ATR
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    results['atr_14'] = tr.rolling(14).mean().iloc[-1]

    # OBV (标准化)
    obv = (np.sign(close.diff()) * volume).cumsum()
    results['obv'] = (obv / obv.abs().max()).iloc[-1] if obv.abs().max() > 0 else np.nan

    # VWAP偏离
    vwap = (close * volume).rolling(5).sum() / volume.rolling(5).sum()
    results['vwap_5'] = ((close - vwap) / vwap).iloc[-1]

    # 波动率
    results['volatility_20'] = close.pct_change().rolling(20).std().iloc[-1]

    # MACD柱
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    results['macd_bar'] = 2 * (dif - dea).iloc[-1]
    results['macd_cross'] = ((dif.shift(1) - dea.shift(1)) * (dif - dea)).iloc[-1]
    results['macd_second_peak'] = dif.diff().diff().iloc[-1]

    # 加速度
    returns = close.pct_change()
    results['acceleration'] = (returns.rolling(5).mean() - returns.rolling(20).mean()).iloc[-1]

    # 突破强度
    max_high_60 = high.rolling(60).max()
    results['breakout_strength'] = ((close - max_high_60.shift(1)) / max_high_60.shift(1)).iloc[-1]

    # 平均成本
    avg_cost = (close * volume).sum() / volume.sum() if volume.sum() > 0 else np.nan
    results['avg_cost'] = (close.iloc[-1] - avg_cost) / avg_cost if not np.isnan(avg_cost) else np.nan

    # 盈利比例
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else np.nan
    profit = 0.0
    if not np.isnan(ma20):
        profit += 0.5 * (1 if close.iloc[-1] > ma20 else 0)
    if not np.isnan(ma60):
        profit += 0.5 * (1 if close.iloc[-1] > ma60 else 0)
    results['profit_ratio'] = profit

    # 筹码集中度
    total_vol = volume.sum()
    if total_vol > 0:
        hist_vol = volume.tail(20).sum() if len(volume) >= 20 else volume.sum()
        results['concentration'] = hist_vol / total_vol
    else:
        results['concentration'] = np.nan

    # CCI
    tp = (high + low + close) / 3
    mad = tp.rolling(20).apply(lambda x: abs(x - x.mean()).mean(), raw=False)
    results['cci_20'] = ((tp - tp.rolling(20).mean()) / (0.015 * mad)).iloc[-1]

    # WR
    high_14 = high.rolling(14).max()
    low_14 = low.rolling(14).min()
    results['wr_14'] = -100 * (tr / high_14.rolling(14).sum()).iloc[-1] if high_14.iloc[-1] > 0 else np.nan

    # 过滤NaN
    return {k: v for k, v in results.items() if not (isinstance(v, float) and np.isnan(v))}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='快速IC滚动计算')
    parser.add_argument('--days', type=int, default=60, help='回算天数')
    args = parser.parse_args()

    print(f'=' * 60)
    print(f'  快速IC滚动计算 @ {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print(f'  回算范围: {args.days} 天')
    print(f'=' * 60)

    conn = sqlite3.connect(DB_PATH)

    # 获取交易日期列表
    dates_row = conn.execute(
        "SELECT DISTINCT date FROM daily_k ORDER BY date DESC LIMIT ?",
        (args.days + 20,)
    ).fetchall()
    all_dates = sorted([r[0] for r in dates_row])

    # 只取最近days天
    target_dates = all_dates[-args.days:] if len(all_dates) >= args.days else all_dates
    print(f"  交易日期范围: {target_dates[0]} ~ {target_dates[-1]} ({len(target_dates)}天)")

    # 检查哪些日期已有IC数据
    store_conn = sqlite3.connect(STORE_DB)
    existing = set(r[0] for r in store_conn.execute(
        "SELECT DISTINCT date FROM ic_history"
    ).fetchall())
    missing_dates = [d for d in target_dates if d not in existing]
    print(f"  已有IC数据: {len(target_dates) - len(missing_dates)}天")
    print(f"  需计算: {len(missing_dates)}天")
    store_conn.close()

    if not missing_dates:
        print("  所有日期IC已存在，无需计算")
        return

    total_start = time.time()
    processed = 0

    for idx, date in enumerate(missing_dates):
        day_start = time.time()
        print(f"\n[{idx+1}/{len(missing_dates)}] 计算 {date}...", end=' ', flush=True)

        # 1. 获取当日所有股票代码
        codes_row = conn.execute(
            "SELECT code FROM daily_k WHERE date = ? "
            "AND code NOT LIKE 'bj.%%' "
            "AND code NOT LIKE 'sh.8%%' AND code NOT LIKE 'sh.9%%' "
            "AND code NOT LIKE 'sh.4%%' AND code NOT LIKE 'sh.68%%' "
            "AND close > 0 AND volume > 0",
            (date,)
        ).fetchall()
        codes = [r[0] for r in codes_row]

        if len(codes) < 100:
            print(f"跳过(股票不足:{len(codes)})")
            continue

        # 2. 获取T+1收益
        next_row = conn.execute(
            "SELECT date FROM daily_k WHERE date > ? "
            "GROUP BY date HAVING COUNT(*) > 100 "
            "ORDER BY date ASC LIMIT 1",
            (date,)
        ).fetchone()
        if not next_row:
            print("跳过(无T+1数据)")
            continue
        next_date = next_row[0]

        fwd_rows = conn.execute(
            "SELECT a.code, (a.close - b.close) / b.close as ret "
            "FROM daily_k a INNER JOIN daily_k b ON a.code = b.code AND b.date = ? "
            "WHERE a.date = ? AND a.code NOT LIKE 'bj.%%' "
            "AND b.close > 0 AND a.close > 0",
            (next_date, date)
        ).fetchall()
        forward_rets = {r[0]: float(r[1]) for r in fwd_rows}

        if len(forward_rets) < 50:
            print(f"跳过(T+1数据不足:{len(forward_rets)})")
            continue

        # 3. 批量获取K线（所有股票最近120日）
        cutoff = (pd.Timestamp(date) - timedelta(days=120)).strftime('%Y-%m-%d')
        kline_rows = conn.execute(
            "SELECT code, date, close, high, low, volume FROM daily_k "
            "WHERE date >= ? AND code IN ({}) ORDER BY code, date".format(
                ','.join(['?' for _ in codes])
            ),
            [cutoff] + codes
        ).fetchall()

        # 按股票分组
        klines_by_code = {}
        current_code = None
        current_rows = []
        for row in kline_rows:
            if row[0] != current_code:
                if current_code and len(current_rows) >= 20:
                    df = pd.DataFrame(current_rows, columns=['date', 'close', 'high', 'low', 'volume'])
                    klines_by_code[current_code] = df
                current_code = row[0]
                current_rows = [row[1:]]
            else:
                current_rows.append(row[1:])
        if current_code and len(current_rows) >= 20:
            df = pd.DataFrame(current_rows, columns=['date', 'close', 'high', 'low', 'volume'])
            klines_by_code[current_code] = df

        # 4. 计算因子值
        factor_values = {}  # {code: {factor: value}}
        valid_codes = list(set(codes) & set(forward_rets.keys()) & set(klines_by_code.keys()))

        for code in valid_codes:
            df = klines_by_code[code]
            try:
                factors = compute_technical_factors(df)
                if factors:
                    factor_values[code] = factors
            except Exception:
                pass

        if len(factor_values) < 30:
            print(f"跳过(有效股票不足:{len(factor_values)})")
            continue

        # 5. 计算IC
        all_factors = set()
        for fv in factor_values.values():
            all_factors.update(fv.keys())

        records = []
        for factor_name in sorted(all_factors):
            factor_vals = []
            rets = []
            for code, fv in factor_values.items():
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
            print(f"    {factor_name}: IC={ic:.4f}", end=' ', flush=True)

        if not records:
            print("无记录")
            continue

        # 6. 保存
        store_conn = sqlite3.connect(STORE_DB)
        for rec in records:
            store_conn.execute(
                "DELETE FROM ic_history WHERE date = ? AND factor_name = ?",
                (rec['date'], rec['factor_name'])
            )
            store_conn.execute(
                "INSERT INTO ic_history (date, factor_name, ic, p_value, n_stocks) VALUES (?, ?, ?, ?, ?)",
                (rec['date'], rec['factor_name'], rec['ic'], rec['p_value'], rec['n_stocks'])
            )
        store_conn.commit()
        store_conn.close()

        elapsed = time.time() - day_start
        processed += 1
        print(f"({len(records)}个因子, {elapsed:.1f}s)")

    total_elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"  完成！处理 {processed}/{len(missing_dates)} 天，总耗时 {total_elapsed:.1f}s")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
