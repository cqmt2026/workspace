"""
Pipeline v2 本地因子回测（factors.db版，不依赖API）
=============================================
从factors.db读取所有非API因子（13个），回测2026年30天。
不依赖API，可以立即跑。
"""
import io
import sys, os, json, sqlite3, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import numpy as np
print = lambda *a, **kw: __builtins__.print(*a, **kw, flush=True)

FACTORS_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'factors.db')
DB = r'F:\market_data.db'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out_data')
os.makedirs(OUT_DIR, exist_ok=True)


def calc_score(f, params):
    """13因子评分（动量+板块+量能+安全，满分60分）"""
    pct = f.get('pct_chg_1d')
    vr = f.get('vol_ratio')
    if pct is None or vr is None: return None
    if pct < params['pct_chg_min'] or pct > params['pct_chg_max']: return None
    if vr <= 0.5: return None

    # 动量 (30分)
    mom = 0.0
    m5, m20, m60 = f.get('ma_5'), f.get('ma_20'), f.get('ma_60')
    if m5 is not None and m20 is not None and m5 > m20:
        mom += 15
        if m60 is not None and m20 > m60: mom += 10
    rs = f.get('relative_strength')
    if rs is not None: mom += max(0, min(5, rs / 2))
    mom = min(mom, 30)

    # 板块 (15分)
    sector = 0.0
    sp = f.get('sector_phase')
    if sp is not None: sector += max(0, min(10, (sp + 5) * 10 / 13))
    srp = f.get('sector_rps_5d')
    if srp is not None: sector += max(0, min(5, srp))
    sector = min(sector, 15)

    # 量能 (10分)
    vol = min(10, min(8, vr * 3)) if vr > 1 else 0

    # 安全 (5分)
    safe = 5.0
    rsi = f.get('rsi_14')
    if rsi is not None and rsi > 80: safe -= 3
    pc5 = f.get('pct_chg_5d')
    if pc5 is not None and pc5 > 20: safe -= 2
    safe = max(0, safe)

    score = (mom * 30 + sector * 15 + vol * 10 + safe * 5) / (30 * 30 + 15 * 15 + 10 * 10 + 5 * 5) * 100
    return score if score >= params['min_score'] else None


def main():
    t0 = time.time()
    print('=' * 60)
    print('  Pipeline v2 本地因子回测')
    print('=' * 60)

    params = {
        'pct_chg_min': 1.5, 'pct_chg_max': 5.0,
        'min_score': 50, 'max_positions': 5,
    }

    if not os.path.exists(FACTORS_DB):
        print(f'factors.db 不存在')
        return

    fconn = sqlite3.connect(FACTORS_DB)

    # 读取所有因子数据
    rows = fconn.execute("SELECT date, code, factor_name, value FROM factors").fetchall()
    print(f'  总行数: {len(rows):,}')

    factor_data = {}
    for d, c, fn, val in rows:
        if (c, d) not in factor_data: factor_data[(c, d)] = {}
        factor_data[(c, d)][fn] = val

    # 获取交易日历（从factor_coverage）
    dates = sorted([r[0] for r in fconn.execute(
        "SELECT date FROM factor_coverage ORDER BY date"
    ).fetchall()])
    print(f'  日期范围: {dates[0]} ~ {dates[-1]} ({len(dates)}天)')

    # 获取候选股票（最新交易日有数据的所有）
    codes = sorted(set(c for c, d in factor_data.keys() if d == dates[-1]))
    print(f'  候选: {len(codes)}只')

    # 读取当日价格
    conn = sqlite3.connect(DB)
    price_data = {}
    codes_str = ','.join(codes)
    ph = ','.join(['?'] * len(codes))
    for date in dates:
        for row in conn.execute(
            f"SELECT code, close FROM daily_k WHERE date=? AND code IN ({ph})",
            [date] + codes
        ).fetchall():
            price_data[(row[0], date)] = float(row[1])
    conn.close()

    print('运行回测...')
    positions = {}
    trades = []
    daily_equity = []
    signal_log = []

    N = len(dates)
    for i, date in enumerate(dates):
        if i % 10 == 0:
            print(f'  {i}/{N} 持仓:{len(positions)}', end='\r')

        day_f = {c: factor_data.get((c, date), {}) for c in codes}
        day_p = {c: price_data.get((c, date), 0) for c in codes}

        # 卖出
        sell = []
        for code, pos in list(positions.items()):
            f = day_f.get(code, {})
            ma20 = f.get('ma_20')
            if ma20 and pos['buy_price'] < ma20:
                sell.append(code)
                continue
            if calc_score(f, params) is None:
                sell.append(code)

        for code in sell:
            pos = positions.pop(code)
            close = day_p.get(code, pos['buy_price'])
            ret = (close - pos['buy_price']) / pos['buy_price'] if pos['buy_price'] > 0 else 0
            trades.append({
                'code': code, 'buy_date': pos['date'], 'sell_date': date,
                'buy_price': pos['buy_price'], 'sell_price': close,
                'return': ret, 'hold_days': i - pos['idx'], 'score': pos['score'],
            })

        # 买入
        remaining = params['max_positions'] - len(positions)
        if remaining > 0:
            scored = [(c, calc_score(f, params)) for c, f in day_f.items() if c not in positions]
            scored = [(c, s) for c, s in scored if s is not None]
            scored.sort(key=lambda x: x[1], reverse=True)
            for code, score in scored[:remaining]:
                close = day_p.get(code, 0)
                if close and close > 0:
                    positions[code] = {'date': date, 'buy_price': close, 'score': score, 'idx': i}
                    signal_log.append({'date': date, 'code': code, 'score': score, 'price': close})

        nav = 1.0
        for code, pos in positions.items():
            close = day_p.get(code, pos['buy_price'])
            if close and pos['buy_price'] > 0:
                nav += 0.2 * (close / pos['buy_price'] - 1)
        daily_equity.append(nav)

    for code, pos in list(positions.items()):
        close = day_p.get(code, pos['buy_price'])
        ret = (close - pos['buy_price']) / pos['buy_price'] if pos['buy_price'] > 0 else 0
        trades.append({
            'code': code, 'buy_date': pos['date'], 'sell_date': dates[-1],
            'buy_price': pos['buy_price'], 'sell_price': close or 0,
            'return': ret, 'hold_days': N - pos['idx'], 'score': pos['score'],
        })

    elapsed = time.time() - t0

    if not trades:
        print('\n无交易!')
        return

    df_t = pd.DataFrame(trades)
    wr = (df_t['return'] > 0).mean()
    aw = df_t[df_t['return'] > 0]['return'].mean() if (df_t['return'] > 0).any() else 0
    al = df_t[df_t['return'] < 0]['return'].mean() if (df_t['return'] < 0).any() else 0
    tr = daily_equity[-1] - 1.0 if daily_equity else 0

    es = pd.Series(daily_equity)
    mdd = ((es - es.expanding().max()) / es.expanding().max()).min()
    ar = (1 + tr) ** (252 / N) - 1 if N > 0 else 0

    print(f'\n{"="*60}')
    print(f'  回测结果')
    print(f'  {"="*60}')
    print(f'  区间:      {dates[0]} ~ {dates[-1]} ({N}天)')
    print(f'  候选:      {len(codes)}只')
    print(f'  总收益率:  {tr:>+7.2%}')
    print(f'  年化收益:  {ar:>+7.2%}')
    print(f'  最大回撤:  {mdd:>7.2%}')
    print(f'  交易次数:  {len(trades)}')
    print(f'  胜率:      {wr:>7.2%}')
    print(f'  平均盈利:  {aw:>+7.2%}')
    print(f'  平均亏损:  {al:>+7.2%}')
    print(f'  盈亏比:    {abs(aw/al):>.2f}' if al != 0 else '')
    print(f'  平均持仓:  {df_t["hold_days"].mean():.1f}天')
    print(f'  耗时:      {elapsed:.0f}s')

    df_t['buy_date'] = pd.to_datetime(df_t['buy_date'])
    df_t['month'] = df_t['buy_date'].dt.to_period('M')
    monthly = df_t.groupby('month').agg(
        交易次数=('return','count'),
        胜率=('return', lambda x: (x>0).mean()),
        平均收益=('return','mean'))
    print(f'\n  按月统计:')
    for m, r in monthly.iterrows():
        print(f'  {m}  {r["交易次数"]:>3}笔 胜率{r["胜率"]:.0%} 均收益{r["平均收益"]:+.2%}')

    df_t['score_bin'] = pd.cut(df_t['score'], bins=[0, 60, 70, 80, 100], labels=['50-60','60-70','70-80','80+'])
    ss = df_t.groupby('score_bin').agg(
        交易次数=('return','count'),
        胜率=('return', lambda x: (x>0).mean()),
        平均收益=('return','mean'))
    print(f'\n  按评分区间:')
    for s, r in ss.iterrows():
        print(f'  {s}分: {r["交易次数"]}笔 胜率{r["胜率"]:.0%} 均收益{r["平均收益"]:+.2%}')

    json.dump({
        'total_return': tr, 'annual_return': ar, 'max_drawdown': mdd,
        'total_trades': len(trades), 'win_rate': wr, 'avg_win': aw, 'avg_loss': al,
        'avg_hold_days': float(df_t['hold_days'].mean()), 'elapsed_sec': elapsed,
    }, open(os.path.join(OUT_DIR, 'backtest_local_factors.json'), 'w'), indent=2)
    df_t.to_csv(os.path.join(OUT_DIR, 'backtest_local_factors_trades.csv'), index=False, encoding='utf-8-sig')
    pd.DataFrame(signal_log).to_csv(os.path.join(OUT_DIR, 'backtest_local_factors_signals.csv'), index=False, encoding='utf-8-sig')

    print(f'\n结果已保存: {OUT_DIR}/')
    print(f'\n完成')


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()