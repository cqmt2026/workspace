"""
Pipeline v2 完整回测引擎（factors.db版）
======================================
从factors.db读取全部35个因子，运行6维度评分回测。
支持两种模式：
  - 全量模式：从factors.db读取所有因子（推荐，等数据积累足够后用）
  - 快速模式：只读技术因子（当前可用）

用法：
  python scripts/run_backtest_pipeline_v2.py --mode full    # 完整35因子
  python scripts/run_backtest_pipeline_v2.py --mode fast    # 仅技术因子
  python scripts/run_backtest_pipeline_v2.py --range 2025   # 指定年份
  python scripts/run_backtest_pipeline_v2.py --range 2026   # 指定年份
"""
import io
import sys, os, json, sqlite3, time, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import numpy as np
print = lambda *a, **kw: __builtins__.print(*a, **kw, flush=True)

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(WORK_DIR, 'out_data')
os.makedirs(OUT_DIR, exist_ok=True)
FACTORS_DB = os.path.join(WORK_DIR, 'data', 'factors.db')
DB = r'F:\market_data.db'


def calc_pipeline_score(f, params):
    """Pipeline v2 6维度评分（满分100分）

    6维度:
    1. 动量趋势 (30分): MA多头+板块阶段+相对强度+5日涨幅
    2. 量能确认 (20分): 放量倍数+资金流强度/持续性
    3. 价格形态 (15分): 突破/反转/底部/回调/确认
    4. 基本面 (15分): PE/PB/市值
    5. 情绪 (10分): MX舆情+ML概率
    6. 安全 (10分): 5日涨幅惩罚+RSI超买
    """
    pct = f.get('pct_chg_1d')
    vr = f.get('vol_ratio')
    if pct is None or vr is None: return None
    if pct < params['pct_chg_min'] or pct > params['pct_chg_max']: return None
    if vr <= 0.5: return None

    # 1. 动量趋势 (30分)
    mom = 0.0
    m5, m20, m60 = f.get('ma_5'), f.get('ma_20'), f.get('ma_60')
    if m5 is not None and m20 is not None and m5 > m20:
        mom += 15
        if m60 is not None and m20 > m60: mom += 10
    sp = f.get('sector_phase')
    if sp is not None: mom += max(0, min(10, (sp + 5) * 10 / 13))
    rs = f.get('relative_strength')
    if rs is not None: mom += max(0, min(5, rs / 2))
    pc5 = f.get('pct_chg_5d')
    if pc5 is not None and 0 < pc5 < 10: mom += min(5, pc5)
    mom = min(mom, 30)

    # 2. 量能确认 (20分)
    vol = 0.0
    if vr > 1: vol += min(8, vr * 3)
    fi = f.get('flow_intensity')
    if fi is not None: vol += min(7, max(0, fi * 50))
    fp = f.get('flow_persistence')
    if fp is not None: vol += fp * 5
    vol = min(vol, 20)

    # 3. 价格形态 (15分)
    pat = 0.0
    for pf, pts in [('pattern_strength', 8), ('pattern_reversal', 5),
                     ('pattern_wbottom', 5), ('pattern_pullback', 6)]:
        if f.get(pf, 0) > 0: pat += pts
    pc_val = f.get('price_confirmation')
    if pc_val is not None: pat += pc_val * 4
    pat = min(pat, 15)

    # 4. 基本面 (15分)
    fund = 0.0
    pe = f.get('pe_ttm')
    if pe is not None and 10 < pe < 50: fund += 5
    pb = f.get('pb')
    if pb is not None and 1 < pb < 10: fund += 5
    mc = f.get('market_cap')
    if mc is not None:
        if 20 < mc < 500: fund += 5
        elif mc <= 20: fund += 3
    fund = min(fund, 15)

    # 5. 情绪 (10分)
    sent = 0.0
    mx = f.get('mx_sentiment')
    if mx is not None: sent += mx
    ml = f.get('ml_prob_lgb')
    if ml is not None and ml > 0.5: sent += min(5, (ml - 0.5) * 20)
    sent = min(sent, 10)

    # 6. 安全 (10分)
    safe = 10.0
    if pc5 is not None:
        if pc5 > 10: safe -= 3
        if pc5 > 20: safe -= 4
    rsi = f.get('rsi_14')
    if rsi is not None and rsi > 80: safe -= 3
    safe = max(0, safe)

    w = params['weights']
    total = (mom * w['momentum'] + vol * w['volume'] + pat * w['pattern']
             + fund * w['fundamental'] + sent * w['sentiment'] + safe * w['safety'])
    max_possible = (30 * w['momentum'] + 20 * w['volume'] + 15 * w['pattern']
                    + 15 * w['fundamental'] + 10 * w['sentiment'] + 10 * w['safety'])
    if max_possible <= 0: return None
    score = total / max_possible * 100
    return score if score >= params['min_score'] else None


def load_full_factors(conn, year=None):
    """从factors.db加载全部因子"""
    if year:
        rows = conn.execute(
            f"SELECT date, code, factor_name, value FROM factors WHERE date LIKE '{year}%'"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT date, code, factor_name, value FROM factors"
        ).fetchall()
    print(f'  总行数: {len(rows):,}')

    factor_data = {}
    for row in rows:
        d, c, fn, val = row
        key = (c, d)
        if key not in factor_data:
            factor_data[key] = {}
        factor_data[key][fn] = val

    return factor_data


def load_fast_factors(conn, year=None, sample_size=500):
    """从market_data.db直接计算技术因子（快速模式）"""
    from alice_quant.features.calculators import TechnicalFactors
    tf = TechnicalFactors()

    if year:
        prefix = f"{year}-"
    else:
        prefix = ""

    dates = [r[0] for r in conn.execute(
        f"SELECT DISTINCT date FROM daily_k WHERE date LIKE '{prefix}%' "
        "AND date IN (SELECT date FROM daily_k GROUP BY date HAVING COUNT(*)>1000) "
        "ORDER BY date"
    ).fetchall()]
    print(f'  交易日: {len(dates)}天 ({dates[0]} ~ {dates[-1]})')

    all_codes = [r[0] for r in conn.execute(
        "SELECT DISTINCT code FROM daily_k WHERE date=? "
        "AND code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%' AND code NOT LIKE 'sh.9%' "
        "AND close>0 AND volume>0", (dates[-1],)
    ).fetchall()]
    np.random.seed(42)
    codes = sorted(np.random.choice(all_codes, size=min(sample_size, len(all_codes)), replace=False))
    print(f'  候选: {len(codes)}只（随机{sample_size}只）')

    factor_data = {}
    price_data = {}

    for code in codes:
        rows = conn.execute(
            "SELECT date, close, volume FROM daily_k WHERE code=? "
            "AND date>=? AND date<=? ORDER BY date",
            (code, dates[0], dates[-1])
        ).fetchall()
        if len(rows) < 20: continue

        closes = np.array([r[1] for r in rows], dtype=np.float64)
        volumes = np.array([r[2] for r in rows], dtype=np.float64)
        dates_raw = list(r[0] for r in rows)

        try:
            df = pd.DataFrame({'close': closes, 'volume': volumes})
            m5 = tf.ma(df['close'], 5)
            m20 = tf.ma(df['close'], 20)
            m60 = tf.ma(df['close'], 60)
            rsi = tf.rsi(df['close'], 14)
            vr = tf.volume_ratio(df['volume'], 5)
            pc1 = tf.pct_change(df['close'], 1)
            pc5s = tf.pct_change(df['close'], 5)

            for j, d in enumerate(dates_raw):
                if d not in set(dates): continue
                day_f = {}
                for fname, s in [('ma_5', m5), ('ma_20', m20), ('ma_60', m60),
                                 ('rsi_14', rsi), ('vol_ratio', vr),
                                 ('pct_chg_1d', pc1), ('pct_chg_5d', pc5s)]:
                    if s is not None and len(s) > j:
                        val = s.iloc[j]
                        if not np.isnan(val) and np.isfinite(val):
                            day_f[fname] = float(val)
                if day_f:
                    factor_data[(code, d)] = day_f
                    price_data[(code, d)] = float(closes[j])
        except: pass

    return factor_data, price_data, dates, codes


def run_backtest(dates, codes, factor_data, params, price_data=None):
    """回测主循环"""
    positions = {}
    trades = []
    daily_equity = []
    signal_log = []
    N = len(dates)

    for i, date in enumerate(dates):
        if i % 50 == 0:
            print(f'  {i}/{N} 持仓:{len(positions)}', end='\r')

        day_f = {c: factor_data.get((c, date), {}) for c in codes}

        # 当日价格
        if price_data:
            day_p = {c: price_data.get((c, date), 0) for c in codes}
        else:
            day_p = {}

        # 卖出
        sell = []
        for code, pos in list(positions.items()):
            f = day_f.get(code, {})
            ma20 = f.get('ma_20')
            if ma20 and pos['buy_price'] < ma20:
                sell.append(code)
                continue
            if calc_pipeline_score(f, params) is None:
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
            scored = [(c, calc_pipeline_score(f, params)) for c, f in day_f.items() if c not in positions]
            scored = [(c, s) for c, s in scored if s is not None]
            scored.sort(key=lambda x: x[1], reverse=True)
            for code, score in scored[:remaining]:
                close = day_p.get(code, 0)
                if close and close > 0:
                    positions[code] = {'date': date, 'buy_price': close, 'score': score, 'idx': i}
                    signal_log.append({'date': date, 'code': code, 'score': score, 'price': close})

        # 净值
        nav = 1.0
        for code, pos in positions.items():
            close = day_p.get(code, pos['buy_price'])
            if close and pos['buy_price'] > 0:
                nav += 0.2 * (close / pos['buy_price'] - 1)
        daily_equity.append(nav)

    # 收盘平仓
    for code, pos in list(positions.items()):
        close = day_p.get(code, pos['buy_price'])
        ret = (close - pos['buy_price']) / pos['buy_price'] if pos['buy_price'] > 0 else 0
        trades.append({
            'code': code, 'buy_date': pos['date'], 'sell_date': dates[-1],
            'buy_price': pos['buy_price'], 'sell_price': close or 0,
            'return': ret, 'hold_days': N - pos['idx'], 'score': pos['score'],
        })

    return trades, daily_equity, signal_log


def report(trades, daily_equity, signal_log, dates, n_codes, mode, elapsed, out_prefix):
    """绩效报告"""
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
    ar = (1 + tr) ** (252 / len(dates)) - 1 if len(dates) > 0 else 0

    print(f'\n{"="*60}')
    print(f'  回测结果 ({mode})')
    print(f'  {"="*60}')
    print(f'  区间:      {dates[0]} ~ {dates[-1]} ({len(dates)}天)')
    print(f'  候选:      {n_codes}只')
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

    # 按月
    df_t['buy_date'] = pd.to_datetime(df_t['buy_date'])
    df_t['month'] = df_t['buy_date'].dt.to_period('M')
    monthly = df_t.groupby('month').agg(
        交易次数=('return','count'),
        胜率=('return', lambda x: (x>0).mean()),
        平均收益=('return','mean'))
    print(f'\n  按月统计:')
    for m, r in monthly.iterrows():
        print(f'  {m}  {r["交易次数"]:>3}笔 胜率{r["胜率"]:.0%} 均收益{r["平均收益"]:+.2%}')

    # 按评分
    df_t['score_bin'] = pd.cut(df_t['score'], bins=[0, 60, 70, 80, 100], labels=['50-60','60-70','70-80','80+'])
    ss = df_t.groupby('score_bin').agg(
        交易次数=('return','count'),
        胜率=('return', lambda x: (x>0).mean()),
        平均收益=('return','mean'))
    print(f'\n  按评分区间:')
    for s, r in ss.iterrows():
        print(f'  {s}分: {r["交易次数"]}笔 胜率{r["胜率"]:.0%} 均收益{r["平均收益"]:+.2%}')

    # 保存
    result = {
        'total_return': tr, 'annual_return': ar, 'max_drawdown': mdd,
        'total_trades': len(trades), 'win_rate': wr, 'avg_win': aw, 'avg_loss': al,
        'avg_hold_days': float(df_t['hold_days'].mean()), 'elapsed_sec': elapsed,
    }
    json.dump(result, open(os.path.join(OUT_DIR, f'{out_prefix}.json'), 'w'), indent=2)
    df_t.to_csv(os.path.join(OUT_DIR, f'{out_prefix}_trades.csv'), index=False, encoding='utf-8-sig')
    pd.DataFrame(signal_log).to_csv(os.path.join(OUT_DIR, f'{out_prefix}_signals.csv'), index=False, encoding='utf-8-sig')

    print(f'\n结果已保存: {OUT_DIR}/')


def main():
    t0 = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['full', 'fast'], default='fast',
                        help='full=完整35因子, fast=仅技术因子')
    parser.add_argument('--year', type=str, default=None,
                        help='指定年份 (2025/2026)')
    parser.add_argument('--sample', type=int, default=500,
                        help='候选股票数量（fast模式）')
    args = parser.parse_args()

    print('=' * 60)
    print(f'  Pipeline v2 完整回测引擎 ({args.mode}模式)')
    print('=' * 60)

    params = {
        'pct_chg_min': 1.5, 'pct_chg_max': 5.0,
        'min_score': 50, 'max_positions': 5,
        'weights': {
            'momentum': 0.30, 'volume': 0.20, 'pattern': 0.15,
            'fundamental': 0.15, 'sentiment': 0.10, 'safety': 0.10,
        }
    }

    conn = sqlite3.connect(DB)

    if args.mode == 'full':
        if not os.path.exists(FACTORS_DB):
            print(f'factors.db 不存在: {FACTORS_DB}')
            print('先运行: python scripts/daily_factor_compute.py --backfill 30')
            return

        fconn = sqlite3.connect(FACTORS_DB)
        factor_data = load_full_factors(fconn, year=args.year)
        fconn.close()

        if not factor_data:
            print('factors.db 无数据!')
            return

        # 提取日期和代码
        dates = sorted(set(d for _, d in factor_data.keys()))
        codes = sorted(set(c for c, _ in factor_data.keys()))
        # 获取价格
        price_data = {}
        for code in codes:
            for date in dates:
                rows = conn.execute(
                    "SELECT close FROM daily_k WHERE code=? AND date=?",
                    (code, date)
                ).fetchall()
                if rows:
                    price_data[(code, date)] = float(rows[0][0])
        print(f'  日期范围: {dates[0]} ~ {dates[-1]} ({len(dates)}天)')
        print(f'  候选: {len(codes)}只')
        n_codes = len(codes)

    else:
        factor_data, price_data, dates, codes = load_fast_factors(conn, year=args.year, sample_size=args.sample)
        n_codes = len(codes)
        if not factor_data:
            print('快速模式无数据!')
            return

    print('运行回测...')
    trades, daily_equity, signal_log = run_backtest(dates, codes, factor_data, params, price_data)

    elapsed = time.time() - t0
    out_prefix = f'backtest_pipeline_v2_{args.mode}_{args.year if args.year else "all"}'
    report(trades, daily_equity, signal_log, dates, n_codes, args.mode, elapsed, out_prefix)
    print(f'\n完成')


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()