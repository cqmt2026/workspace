"""
H-002 回测: RPS>80 + 均线多头排列
"""

import sqlite3
import numpy as np
import pandas as pd
import json
import os

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\market_data.db'
OUTPUT_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ma_backtest'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def get_sample_codes(n=300):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT code FROM daily_k 
        GROUP BY code 
        HAVING COUNT(*) >= 500
        ORDER BY RANDOM() 
        LIMIT ?
    """, (n,))
    codes = [r[0] for r in cur.fetchall()]
    conn.close()
    return codes

def load_data(codes):
    log("加载数据到内存...")
    codes_str = ','.join([f"'{c}'" for c in codes])
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"""
        SELECT code, date, close FROM daily_k 
        WHERE code IN ({codes_str})
        ORDER BY code, date
    """, conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date'])
    
    log("计算指标...")
    rows = []
    for code, grp in df.groupby('code'):
        grp = grp.sort_values('date').copy()
        grp['ma5'] = grp['close'].rolling(5).mean()
        grp['ma10'] = grp['close'].rolling(10).mean()
        grp['ma20'] = grp['close'].rolling(20).mean()
        grp['ma5_prev'] = grp['ma5'].shift(1)
        grp['ma10_prev'] = grp['ma10'].shift(1)
        grp['ma20_prev'] = grp['ma20'].shift(1)
        grp['is_bullish'] = (
            (grp['ma5'] > grp['ma10']) & (grp['ma10'] > grp['ma20']) &
            (grp['ma5'] > grp['ma5_prev']) & (grp['ma10'] > grp['ma10_prev']) & (grp['ma20'] > grp['ma20_prev'])
        )
        grp['ret_20d'] = grp['close'].pct_change(20)
        grp['code'] = code
        rows.append(grp[['code', 'date', 'close', 'ma5', 'ma10', 'ma20', 'is_bullish', 'ret_20d']])
    
    result = pd.concat(rows, ignore_index=True)
    log(f"数据加载完成: {len(result):,} 条")
    return result

def get_monthly_dates(start='2019-06-01', end='2026-04-01'):
    return list(pd.date_range(start=start, end=end, freq='MS'))

def run_backtest_single(df, hold_days, signal_dates, codes):
    """单持仓周期回测"""
    all_dates = sorted(df['date'].unique())
    date_to_idx = {d: i for i, d in enumerate(all_dates)}
    
    results = {'hm_bull': [], 'hm_non_bull': [], 'all_bull': [], 'all_non_bull': []}
    
    for i, sig_dt in enumerate(signal_dates):
        sig_dt = pd.to_datetime(sig_dt)
        
        pre = df[df['date'] <= sig_dt]
        if pre.empty:
            continue
        
        last = pre.loc[pre.groupby('code')['date'].idxmax()].copy()
        last = last[last['close'] > 0]
        
        if len(last) < 10:
            continue
        
        # RPS>80 模拟
        threshold = last['ret_20d'].quantile(0.80)
        high_mom = last[last['ret_20d'] >= threshold]
        
        hm_bull = high_mom[high_mom['is_bullish'] == True]
        hm_non_bull = high_mom[high_mom['is_bullish'] == False]
        all_bull = last[last['is_bullish'] == True]
        all_non_bull = last[~last['code'].isin(all_bull['code'])]
        
        # 买入日
        sig_idx = date_to_idx.get(sig_dt)
        if sig_idx is None:
            nxt = [j for j, d in enumerate(all_dates) if d > sig_dt]
            if not nxt: continue
            buy_idx = nxt[0]
        else:
            nxt = [j for j, d in enumerate(all_dates) if j > sig_idx]
            if not nxt: continue
            buy_idx = nxt[0]
        
        sell_idx = buy_idx + hold_days
        if sell_idx >= len(all_dates):
            continue
        
        buy_date = all_dates[buy_idx]
        sell_date = all_dates[sell_idx]
        
        buy_prices = df[df['date'] == buy_date].set_index('code')['close']
        sell_prices = df[df['date'] == sell_date].set_index('code')['close']
        
        def calc_rets(grp_df):
            out = []
            for _, row in grp_df.iterrows():
                code = row['code']
                if code in buy_prices.index and code in sell_prices.index:
                    bp = buy_prices[code]
                    sp = sell_prices[code]
                    if bp > 0 and sp > 0:
                        out.append({'code': code, 'return': (sp - bp) / bp})
            return out
        
        results['hm_bull'].extend(calc_rets(hm_bull))
        results['hm_non_bull'].extend(calc_rets(hm_non_bull))
        results['all_bull'].extend(calc_rets(all_bull))
        results['all_non_bull'].extend(calc_rets(all_non_bull))
        
        if (i + 1) % 20 == 0:
            log(f"  hold={hold_days}d: {i+1}/{len(signal_dates)}")
    
    return results

def analyze_and_save(all_results_by_hold):
    names = {
        'hm_bull': '高动量+多头排列 (H-002核心)',
        'hm_non_bull': '高动量+非多头排列',
        'all_bull': '全部多头排列 (H-001对照)',
        'all_non_bull': '全部非多头排列'
    }
    
    reports = []
    json_summary = {}
    
    for hold_days, results in all_results_by_hold.items():
        report = [f"\n{'='*55}", f"持仓 {hold_days} 日 - H-002 RPS>80+多头排列", f"{'='*55}"]
        json_summary[hold_days] = {}
        
        for grp_name, trades in results.items():
            name = names[grp_name]
            if not trades:
                report.append(f"\n{name}: 无数据")
                json_summary[hold_days][grp_name] = {'count': 0}
                continue
            
            rets = np.array([t['return'] for t in trades])
            wins = rets[rets > 0]
            losses = rets[rets < 0]
            
            wr = len(wins) / len(rets)
            avg = rets.mean()
            std = rets.std()
            sharpe = (avg * 12) / (std * np.sqrt(12)) if std > 0 else 0
            pl = abs(wins.mean() / losses.mean()) if len(losses) > 0 and losses.mean() != 0 else 0
            
            report.append(f"\n{name}:")
            report.append(f"  交易: {len(rets)}笔  胜率: {wr:.1%}  均收益: {avg:.2%}  夏普: {sharpe:.2f}  盈亏比: {pl:.2f}")
            report.append(f"  最大盈利: {rets.max():.2%}  最大亏损: {rets.min():.2%}")
            
            pd.DataFrame(trades).to_csv(f"{OUTPUT_DIR}/h002_trades_{hold_days}d_{grp_name}.csv", index=False)
            
            json_summary[hold_days][grp_name] = {
                'count': len(rets), 'win_rate': round(wr, 4),
                'avg_return': round(avg, 6), 'sharpe': round(sharpe, 4),
                'pl_ratio': round(pl, 4), 'max_win': round(rets.max(), 6),
                'max_loss': round(rets.min(), 6)
            }
        
        reports.append("\n".join(report))
    
    # H-002核心比较
    comparison = ["\n" + "=" * 55, "H-002 核心结论", "=" * 55]
    
    for hold_days, results in all_results_by_hold.items():
        comparison.append(f"\n持仓{hold_days}日:")
        
        def stat(trades):
            if not trades: return "无数据", "无数据"
            rets = [t['return'] for t in trades]
            wr = sum(1 for r in rets if r > 0) / len(rets)
            avg = np.mean(rets)
            return f"胜率{wr:.1%}", f"均收益{avg:.2%}"
        
        comparison.append(f"  高动量+多头排列: {stat(results['hm_bull'])[0]}, {stat(results['hm_bull'])[1]}")
        comparison.append(f"  高动量+非多头:   {stat(results['hm_non_bull'])[0]}, {stat(results['hm_non_bull'])[1]}")
        comparison.append(f"  全部多头排列:   {stat(results['all_bull'])[0]}, {stat(results['all_bull'])[1]}")
        comparison.append(f"  全部非多头:     {stat(results['all_non_bull'])[0]}, {stat(results['all_non_bull'])[1]}")
        
        hm_bull = results['hm_bull']
        all_bull = results['all_bull']
        if hm_bull and all_bull:
            hm_wr = sum(1 for t in hm_bull if t['return'] > 0) / len(hm_bull)
            all_wr = sum(1 for t in all_bull if t['return'] > 0) / len(all_bull)
            hm_avg = np.mean([t['return'] for t in hm_bull])
            all_avg = np.mean([t['return'] for t in all_bull])
            comparison.append(f"  → RPS过滤效果: 胜率差{(hm_wr-all_wr):.1%}, 均收益差{(hm_avg-all_avg):.2%}")
    
    comp_text = "\n".join(comparison)
    print(comp_text)
    reports.append(comp_text)
    
    with open(f"{OUTPUT_DIR}/h002_backtest_report.txt", 'w', encoding='utf-8') as f:
        f.write("\n".join(reports))
    with open(f"{OUTPUT_DIR}/h002_backtest_summary.json", 'w', encoding='utf-8') as f:
        json.dump(json_summary, f, ensure_ascii=False, indent=2)
    
    log(f"\n已保存: {OUTPUT_DIR}/")

def main():
    log("=" * 55)
    log("H-002 回测: RPS>80 + 均线多头排列")
    log("=" * 55)
    
    codes = get_sample_codes(300)
    signal_dates = get_monthly_dates()
    log(f"样本: {len(codes)}只, 月度信号: {len(signal_dates)}个")
    
    df = load_data(codes)
    
    all_results_by_hold = {}
    for hold_days in [5, 10]:
        log(f"\n--- 持仓 {hold_days} 日 ---")
        results = run_backtest_single(df, hold_days, signal_dates, codes)
        all_results_by_hold[hold_days] = results
    
    analyze_and_save(all_results_by_hold)

if __name__ == '__main__':
    main()