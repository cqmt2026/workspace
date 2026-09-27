"""
Pipeline v2 三年长周期回测（2023-2025）
====================================
从DB直接计算技术+板块因子，跑3年全市场回测。
目的：参数定标 + 权重验证 + 市场状态分析

数据：F:\market_data.db
因子：13个（10技术 + 3板块）
候选：500只（随机，可调）
"""
import io
import sys, os, json, sqlite3, time, multiprocessing as mp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import numpy as np
from datetime import datetime
print = lambda *a, **kw: __builtins__.print(*a, **kw, flush=True)

DB = r'F:\market_data.db'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out_data')
os.makedirs(OUT_DIR, exist_ok=True)

# ========== 策略参数 ==========
PARAMS = {
    'pct_chg_min': 1.5, 'pct_chg_max': 5.0,
    'min_score': 50, 'max_positions': 5,
}

# 权重方案（待优化）
WEIGHT_SCHEMES = {
    'default':   {'mom': 30, 'sec': 15, 'vol': 10, 'safe': 5},  # 当前
    'momentum':  {'mom': 40, 'sec': 10, 'vol': 5,  'safe': 5},  # 强动量
    'volume':    {'mom': 20, 'sec': 10, 'vol': 25, 'safe': 5},  # 重量能
    'balanced':  {'mom': 25, 'sec': 20, 'vol': 10, 'safe': 5},  # 均衡
}


def calc_score(f, params, weights):
    """13因子评分"""
    pct = f.get('pct_chg_1d')
    vr = f.get('vol_ratio')
    if pct is None or vr is None: return None
    if pct < params['pct_chg_min'] or pct > params['pct_chg_max']: return None
    if vr <= 0.5: return None

    # 动量
    mom = 0.0
    m5, m20, m60 = f.get('ma_5'), f.get('ma_20'), f.get('ma_60')
    if m5 is not None and m20 is not None and m5 > m20:
        mom += 15
        if m60 is not None and m20 > m60: mom += 10
    rs = f.get('relative_strength')
    if rs is not None: mom += max(0, min(5, rs / 2))
    mom = min(mom, 30)

    # 板块
    sector = 0.0
    sp = f.get('sector_phase')
    if sp is not None: sector += max(0, min(10, (sp + 5) * 10 / 13))
    srp = f.get('sector_rps_5d')
    if srp is not None: sector += max(0, min(5, srp))
    sector = min(sector, 15)

    # 量能
    vol = min(10, min(8, vr * 3)) if vr > 1 else 0

    # 安全
    safe = 5.0
    rsi = f.get('rsi_14')
    if rsi is not None and rsi > 80: safe -= 3
    pc5 = f.get('pct_chg_5d')
    if pc5 is not None and pc5 > 20: safe -= 2
    safe = max(0, safe)

    w = weights
    max_possible = 30*w['mom'] + 15*w['sec'] + 10*w['vol'] + 5*w['safe']
    if max_possible <= 0: return None
    score = (mom*w['mom'] + sector*w['sec'] + vol*w['vol'] + safe*w['safe']) / max_possible * 100
    return score if score >= params['min_score'] else None


def load_data(conn, dates, codes):
    """批量加载K线 + 计算因子"""
    from alice_quant.features.calculators import TechnicalFactors
    tf = TechnicalFactors()
    date_set = set(dates)

    # 批量拉取所有K线
    rows = conn.execute(
        f"SELECT code, date, close, volume FROM daily_k WHERE code IN "
        f"({','.join(['?']*len(codes))}) AND date>=? AND date<=? ORDER BY code, date",
        codes + [dates[0], dates[-1]]
    ).fetchall()
    print(f'  K线行数: {len(rows):,}')

    # 按code组织
    code_bars = {}
    for code, d, close, vol in rows:
        if code not in code_bars: code_bars[code] = {'dates': [], 'closes': [], 'volumes': []}
        code_bars[code]['dates'].append(d)
        code_bars[code]['closes'].append(float(close))
        code_bars[code]['volumes'].append(float(vol))

    # 计算因子
    factor_cache = {}
    price_cache = {}
    for code, bars in code_bars.items():
        if len(bars['closes']) < 60: continue
        df = pd.DataFrame({'close': bars['closes'], 'volume': bars['volumes']})
        try:
            m5 = tf.ma(df['close'], 5)
            m20 = tf.ma(df['close'], 20)
            m60 = tf.ma(df['close'], 60)
            rsi = tf.rsi(df['close'], 14)
            vr = tf.volume_ratio(df['volume'], 5)
            pc1 = tf.pct_change(df['close'], 1)
            pc5 = tf.pct_change(df['close'], 5)

            fc = {}
            pc = {}
            for j, d in enumerate(bars['dates']):
                if d not in date_set: continue
                day_f = {}
                for fname, s in [('ma_5', m5), ('ma_20', m20), ('ma_60', m60),
                                 ('rsi_14', rsi), ('vol_ratio', vr),
                                 ('pct_chg_1d', pc1), ('pct_chg_5d', pc5)]:
                    if s is not None and len(s) > j:
                        val = s.iloc[j]
                        if not np.isnan(val) and np.isfinite(val):
                            day_f[fname] = float(val)
                if day_f:
                    fc[d] = day_f
                pc[d] = float(bars['closes'][j])
            if fc:
                factor_cache[code] = fc
                price_cache[code] = pc
        except: pass

    # 板块因子（从factors.db读取）
    fdb = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'factors.db')
    if os.path.exists(fdb):
        fconn = sqlite3.connect(fdb)
        srows = fconn.execute("SELECT date, code, factor_name, value FROM factors WHERE factor_name LIKE 'sector_%'").fetchall()
        fconn.close()
        for d, c, fn, val in srows:
            if c in factor_cache and d in factor_cache[c]:
                factor_cache[c][d][fn] = val

    return factor_cache, price_cache


def run_backtest_one(dates, codes, factor_cache, price_cache, params, weights, scheme_name):
    """单次回测"""
    positions = {}
    trades = []
    daily_equity = []
    N = len(dates)

    for i, date in enumerate(dates):
        day_f = {c: factor_cache.get(c, {}).get(date, {}) for c in codes}
        day_p = {c: price_cache.get(c, {}).get(date, 0) for c in codes}

        sell = []
        for code, pos in list(positions.items()):
            f = day_f.get(code, {})
            ma20 = f.get('ma_20')
            if ma20 and pos['buy_price'] < ma20:
                sell.append(code)
                continue
            if calc_score(f, params, weights) is None:
                sell.append(code)

        for code in sell:
            pos = positions.pop(code)
            close = day_p.get(code, pos['buy_price'])
            ret = (close - pos['buy_price']) / pos['buy_price'] if pos['buy_price'] > 0 else 0
            trades.append({'code': code, 'buy_date': pos['date'], 'sell_date': date,
                           'buy_price': pos['buy_price'], 'sell_price': close,
                           'return': ret, 'hold_days': i - pos['idx'], 'score': pos['score']})

        remaining = params['max_positions'] - len(positions)
        if remaining > 0:
            scored = [(c, calc_score(f, params, weights)) for c, f in day_f.items() if c not in positions]
            scored = [(c, s) for c, s in scored if s is not None]
            scored.sort(key=lambda x: x[1], reverse=True)
            for code, score in scored[:remaining]:
                close = day_p.get(code, 0)
                if close and close > 0:
                    positions[code] = {'date': date, 'buy_price': close, 'score': score, 'idx': i}

        nav = 1.0
        for code, pos in positions.items():
            close = day_p.get(code, pos['buy_price'])
            if close and pos['buy_price'] > 0:
                nav += 0.2 * (close / pos['buy_price'] - 1)
        daily_equity.append(nav)

    for code, pos in list(positions.items()):
        close = day_p.get(code, pos['buy_price'])
        ret = (close - pos['buy_price']) / pos['buy_price'] if pos['buy_price'] > 0 else 0
        trades.append({'code': code, 'buy_date': pos['date'], 'sell_date': dates[-1],
                       'buy_price': pos['buy_price'], 'sell_price': close or 0,
                       'return': ret, 'hold_days': N - pos['idx'], 'score': pos['score']})

    return trades, daily_equity


def report(trades, daily_equity, dates, n_codes, weights, scheme_name):
    """绩效报告"""
    if not trades: return None
    df_t = pd.DataFrame(trades)
    wr = (df_t['return'] > 0).mean()
    aw = df_t[df_t['return'] > 0]['return'].mean() if (df_t['return'] > 0).any() else 0
    al = df_t[df_t['return'] < 0]['return'].mean() if (df_t['return'] < 0).any() else 0
    tr = daily_equity[-1] - 1.0 if daily_equity else 0
    es = pd.Series(daily_equity)
    mdd = ((es - es.expanding().max()) / es.expanding().max()).min()
    ar = (1 + tr) ** (252 / len(dates)) - 1 if len(dates) > 0 else 0

    # 年度统计
    df_t['buy_date'] = pd.to_datetime(df_t['buy_date'])
    df_t['year'] = df_t['buy_date'].dt.year
    annual = df_t.groupby('year').agg(
        交易次数=('return','count'), 胜率=('return', lambda x: (x>0).mean()),
        平均收益=('return','mean'))

    print(f'\n  [{scheme_name}]')
    print(f'  总收益率:  {tr:>+7.2%}  年化: {ar:>+7.2%}  回撤: {mdd:>7.2%}')
    print(f'  交易: {len(trades)}笔  胜率: {wr:>7.2%}  盈亏比: {abs(aw/al):>.2f}' if al != 0 else '')
    print(f'  盈利: {aw:>+7.2%}  亏损: {al:>+7.2%}  持仓: {df_t["hold_days"].mean():.1f}天')
    for y, r in annual.iterrows():
        print(f'  {y}: {r["交易次数"]}笔 胜率{r["胜率"]:.0%} 均收益{r["平均收益"]:+.2%}')

    return {
        'scheme': scheme_name, 'weights': weights,
        'total_return': tr, 'annual_return': ar, 'max_drawdown': mdd,
        'total_trades': len(trades), 'win_rate': wr, 'avg_win': aw, 'avg_loss': al,
        'avg_hold_days': float(df_t['hold_days'].mean()),
    }


def main():
    t0 = time.time()
    print('=' * 60)
    print('  Pipeline v2 三年长周期回测')
    print('=' * 60)

    conn = sqlite3.connect(DB)

    # 交易日
    dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM daily_k WHERE date>='2023-01-01' AND date<='2025-12-31' "
        "AND date IN (SELECT date FROM daily_k GROUP BY date HAVING COUNT(*)>1000) ORDER BY date"
    ).fetchall()]
    print(f'交易日: {len(dates)}天 ({dates[0]} ~ {dates[-1]})')

    # 候选500只（固定种子，可复现）
    all_codes = [r[0] for r in conn.execute(
        "SELECT DISTINCT code FROM daily_k WHERE date=? "
        "AND code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%' AND code NOT LIKE 'sh.9%' "
        "AND close>0 AND volume>0", (dates[-1],)
    ).fetchall()]
    np.random.seed(42)
    codes = sorted(np.random.choice(all_codes, size=500, replace=False))
    print(f'候选: 500只')

    # 加载数据
    print('加载数据...')
    factor_cache, price_cache = load_data(conn, dates, codes)
    conn.close()
    print(f'  有数据股票: {len(factor_cache)}只')

    # 跑4种权重方案
    results = []
    print('运行回测...')
    for sname, weights in WEIGHT_SCHEMES.items():
        trades, de = run_backtest_one(dates, codes, factor_cache, price_cache, PARAMS, weights, sname)
        r = report(trades, de, dates, len(codes), weights, sname)
        if r: results.append(r)

    elapsed = time.time() - t0
    print(f'\n{"="*60}')
    print(f'  权重方案对比')
    print(f'  {"="*60}')
    for r in results:
        print(f'  {r["scheme"]:>10}: 年化{r["annual_return"]:>+7.2%} 胜率{r["win_rate"]:>7.2%}  '
              f'回撤{r["max_drawdown"]:>7.2%} 交易{r["total_trades"]}笔')
    print(f'\n总耗时: {elapsed:.0f}s')

    # 保存
    json.dump(results, open(os.path.join(OUT_DIR, 'backtest_3y_weights.json'), 'w'), indent=2, ensure_ascii=False)
    print(f'结果已保存: {OUT_DIR}/backtest_3y_weights.json')


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()