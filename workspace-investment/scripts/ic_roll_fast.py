# -*- coding: utf-8 -*-
"""Fast IC roll-up computation"""
import sys, os, json, sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

WORK_DIR = r'C:/Users/Administrator/.openclaw/workspace/workspace-investment'
sys.path.insert(0, WORK_DIR)
DB_PATH = r'F:/market_data.db'
FACTORS_DB = os.path.join(WORK_DIR, 'data', 'factors.db')

def compute_all_factors(close, high, low, volume):
    """Vectorized factor computation for one stock."""
    f = {}
    # MA ratios
    for p in [5, 10, 20, 60]:
        ma = close.rolling(p).mean()
        v = (close / ma - 1).iloc[-1]
        f[f'ma_{p}'] = float(v) if not np.isnan(v) else np.nan
    
    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - 100 / (1 + rs)
    f['rsi_14'] = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else np.nan
    
    # Vol ratio
    f['vol_ratio'] = float((volume / volume.rolling(20).mean()).iloc[-1]) if not np.isnan(volume.rolling(20).mean().iloc[-1]) else np.nan
    
    # pct_chg
    for p in [1, 5, 10]:
        pc = close.pct_change(p).iloc[-1]
        f[f'pct_chg_{p}d'] = float(pc) if not np.isnan(pc) else np.nan
    
    # OBV
    obv = (np.sign(close.diff()) * volume).cumsum()
    if obv.abs().max() > 0:
        f['obv'] = float((obv / obv.abs().max()).iloc[-1])
    else:
        f['obv'] = float(obv.iloc[-1])
    
    # VWAP-5
    vwap = (close * volume).rolling(5).sum() / volume.rolling(5).sum()
    f['vwap_5'] = float(((close - vwap) / vwap).iloc[-1]) if not np.isnan(vwap.iloc[-1]) else np.nan
    
    # Volatility
    f['volatility_20'] = float(close.pct_change().rolling(20).std().iloc[-1]) if not np.isnan(close.pct_change().rolling(20).std().iloc[-1]) else np.nan
    
    # MACD bar
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    f['macd_bar'] = float((2 * (dif - dea)).iloc[-1]) if not np.isnan((2 * (dif - dea)).iloc[-1]) else np.nan
    
    # MACD cross
    cross = (dif.shift(1) - dea.shift(1)) * (dif - dea)
    f['macd_cross'] = float(cross.iloc[-1]) if not np.isnan(cross.iloc[-1]) else np.nan
    
    # Acceleration
    rets = close.pct_change()
    f['acceleration'] = float((rets.rolling(5).mean() - rets.rolling(20).mean()).iloc[-1]) if not np.isnan((rets.rolling(5).mean() - rets.rolling(20).mean()).iloc[-1]) else np.nan
    
    # Breakout
    max_h = high.rolling(60).max()
    f['breakout_strength'] = float(((close - max_h.shift(1)) / max_h.shift(1)).iloc[-1]) if not np.isnan((close - max_h.shift(1)).iloc[-1]) else np.nan
    
    # Avg cost
    tv = volume.sum()
    if tv > 0:
        avg = (close * volume).sum() / tv
        f['avg_cost'] = float((close.iloc[-1] - avg) / avg)
    
    # Profit ratio
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else np.nan
    pr = 0.0
    if not np.isnan(ma20):
        pr += 0.5 * (1 if close.iloc[-1] > ma20 else 0)
    if not np.isnan(ma60):
        pr += 0.5 * (1 if close.iloc[-1] > ma60 else 0)
    f['profit_ratio'] = float(pr)
    
    # Concentration
    hv = volume.tail(20).sum() if len(volume) >= 20 else volume.sum()
    f['concentration'] = float(hv / tv) if tv > 0 else np.nan
    
    return f

def main():
    print(f"IC滚动计算 (60天)")
    print("=" * 50)
    
    mkt_conn = sqlite3.connect(DB_PATH)
    store_conn = sqlite3.connect(FACTORS_DB)
    
    max_date = mkt_conn.execute("SELECT MAX(date) FROM daily_k").fetchone()[0]
    prev_date = mkt_conn.execute("SELECT MAX(date) FROM daily_k WHERE date < ?", (max_date,)).fetchone()[0]
    print(f"K线截止: {max_date}, 上一交易日: {prev_date}")
    
    # Get all trading dates in range - compute missing dates between last IC and max K-line date
    rows = mkt_conn.execute(
        "SELECT DISTINCT date FROM daily_k WHERE date <= ? ORDER BY date DESC LIMIT 70",
        (max_date,)
    ).fetchall()
    all_dates = sorted([r[0] for r in rows])
    
    # Find the latest date with IC data
    ic_rows = store_conn.execute("SELECT MAX(date) FROM ic_history").fetchone()
    last_ic_date = ic_rows[0] if ic_rows else None
    print(f"K线截止: {max_date}, 上次IC: {last_ic_date}")
    
    # Compute dates AFTER last IC date up to max_date
    if last_ic_date:
        pending = [d for d in all_dates if d > last_ic_date and d <= max_date]
    else:
        pending = all_dates
    print(f"待计算: {len(pending)} 天 -> {pending[:10]}{'...' if len(pending)>10 else ''}")
    
    # Filter: only dates with enough codes (>=3000 stocks to be useful)
    valid_pending = []
    for d in pending:
        cnt = mkt_conn.execute("SELECT COUNT(*) FROM daily_k WHERE date=? AND close>0 AND volume>0", (d,)).fetchone()[0]
        if cnt >= 3000:
            valid_pending.append(d)
        else:
            print(f"  跳过 {d}: 仅 {cnt} 只股票")
    pending = valid_pending
    
    if not pending:
        print("无需计算")
        mkt_conn.close()
        store_conn.close()
        return
    
    for target_date in pending:
        t0 = __import__('time').time()
        print(f"\n--- {target_date} ---")
        
        # Get codes
        codes = [r[0] for r in mkt_conn.execute(
            "SELECT code FROM daily_k WHERE date = ? AND code NOT LIKE 'bj.%' AND close > 0 AND volume > 0",
            (target_date,)
        )]
        if len(codes) < 100:
            print(f"  Skip: {len(codes)} codes")
            continue
        
        # Next trading date
        next_row = mkt_conn.execute(
            "SELECT date FROM daily_k WHERE date > ? GROUP BY date HAVING COUNT(*) > 100 ORDER BY date ASC LIMIT 1",
            (target_date,)
        ).fetchone()
        if not next_row:
            print(f"  Skip: no next date")
            continue
        next_date = next_row[0]
        
        # Forward returns
        ret_rows = mkt_conn.execute("""
            SELECT a.code, (a.close - b.close) / b.close as ret
            FROM daily_k a INNER JOIN daily_k b ON a.code = b.code AND b.date = ?
            WHERE a.date = ? AND a.code NOT LIKE 'bj.%' AND b.close > 0 AND a.close > 0
        """, (next_date, target_date)).fetchall()
        forward_rets = {r[0]: float(r[1]) for r in ret_rows}
        if len(forward_rets) < 50:
            print(f"  Skip: {len(forward_rets)} forward returns")
            continue
        print(f"  Codes: {len(codes)}, Forward: {len(forward_rets)}")
        
        # Bulk K-line
        min_date = (pd.Timestamp(target_date) - timedelta(days=120)).strftime('%Y-%m-%d')
        kline_rows = mkt_conn.execute("""
            SELECT code, date, close, high, low, volume FROM daily_k
            WHERE date >= ? AND date <= ? ORDER BY code, date ASC
        """, (min_date, next_date)).fetchall()
        
        klines = defaultdict(list)
        for code, d, c, h, l, v in kline_rows:
            klines[code].append((d, c, h, l, v))
        
        # Compute factors
        factor_values = {}
        for code, rows in klines.items():
            if code not in forward_rets or len(rows) < 20:
                continue
            df = pd.DataFrame(rows, columns=['date','close','high','low','volume'])
            try:
                f = compute_all_factors(df['close'], df['high'], df['low'], df['volume'])
                factor_values[code] = f
            except Exception as e:
                pass
        
        print(f"  Valid: {len(factor_values)} stocks, time: {time.time()-t0:.1f}s")
        
        # Compute IC
        all_factors = set()
        for fv in factor_values.values():
            all_factors.update(fv.keys())
        
        records = []
        for fname in sorted(all_factors):
            vals, rets = [], []
            for code, fv in factor_values.items():
                if fname in fv and not np.isnan(fv[fname]):
                    vals.append(fv[fname])
                    rets.append(forward_rets[code])
            if len(vals) < 30:
                continue
            ic, pval = spearmanr(vals, rets)
            records.append({
                'date': target_date, 'factor_name': fname,
                'ic': float(ic), 'p_value': float(pval) if not np.isnan(pval) else None,
                'n_stocks': len(vals),
            })
            print(f"    {fname}: IC={ic:.4f}, p={pval:.4f}")
        
        # Save
        for r in records:
            store_conn.execute("DELETE FROM ic_history WHERE date=? AND factor_name=?",
                              (r['date'], r['factor_name']))
            store_conn.execute(
                "INSERT INTO ic_history (date,factor_name,ic,p_value,n_stocks) VALUES (?,?,?,?,?)",
                (r['date'], r['factor_name'], r['ic'], r['p_value'], r['n_stocks'])
            )
        store_conn.commit()
        print(f"  Saved {len(records)} records, total time: {time.time()-t0:.1f}s")
    
    # Update factor_status
    print("\n更新因子状态...")
    store_conn.execute("""
        CREATE TABLE IF NOT EXISTS factor_status (
            factor_name TEXT PRIMARY KEY, category TEXT, mean_ic REAL,
            ic_ir REAL, positive_ratio REAL, n_days INTEGER, status TEXT, last_updated TEXT
        )
    """)
    
    rows = store_conn.execute("SELECT factor_name, ic, p_value FROM ic_history ORDER BY date DESC").fetchall()
    stats = {}
    for fname, ic, pv in rows:
        if fname not in stats:
            stats[fname] = {'ics': [], 'pvs': []}
        stats[fname]['ics'].append(ic)
        if pv is not None:
            stats[fname]['pvs'].append(pv)
    
    for fname, s in stats.items():
        ics = s['ics'][:20]
        pvs = s['pvs']
        if not ics:
            continue
        mi = float(np.mean(ics))
        ir = mi / float(np.std(ics)) if np.std(ics) > 0 else 0.0
        pr = sum(1 for x in ics if x > 0) / len(ics)
        st = 'eliminated' if abs(mi) < 0.02 and pvs and np.mean(pvs) > 0.1 else 'active'
        store_conn.execute("""
            INSERT INTO factor_status VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(factor_name) DO UPDATE SET
                mean_ic=excluded.mean_ic, ic_ir=excluded.ic_ir,
                positive_ratio=excluded.positive_ratio, n_days=excluded.n_days,
                status=excluded.status, last_updated=excluded.last_updated
        """, (fname, 'technical', mi, ir, pr, len(ics), st, datetime.now().strftime('%Y-%m-%d')))
    store_conn.commit()
    
    # Report
    all_ic_records = store_conn.execute("SELECT date, factor_name, ic, p_value, n_stocks FROM ic_history ORDER BY date DESC").fetchall()
    
    if all_ic_records:
        dates = sorted(set(r[0] for r in all_ic_records))
        records_out = [{'date': r[0], 'factor_name': r[1], 'ic': r[2], 'p_value': r[3], 'n_stocks': r[4]} for r in all_ic_records]
        report = {
            'dates': dates,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_records': len(records_out),
            'records': records_out,
            'summary': {
                'avg_ic': float(np.mean([r['ic'] for r in records_out])),
                'max_ic': float(max([r['ic'] for r in records_out], key=abs)),
                'significant': sum(1 for r in records_out if r['p_value'] is not None and r['p_value'] < 0.05),
            }
        }
        out_dir = os.path.join(WORK_DIR, 'out_data')
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, f'ic_report_{dates[-1]}.json'), 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n完成！报告: out_data/ic_report_{dates[-1]}.json, 共{len(records_out)}条记录")
    else:
        print("\n无IC数据可生成报告")
    
    mkt_conn.close()
    store_conn.close()

if __name__ == '__main__':
    main()
