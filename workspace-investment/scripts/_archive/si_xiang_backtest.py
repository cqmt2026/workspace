# -*- coding: utf-8 -*-
"""
四象共振底部反转 · 历史回测 v4
直接用今日扫描逻辑，在历史上每个月末跑一次全市场扫描
记录：如果信号出现，买入持有60个交易日的收益

关键改进：在历史上每个月的最后交易日，执行一次全市场扫描
完全模拟 si_xiang_bottom_scan.py v1.1 的逻辑
"""
import sqlite3, pandas as pd, numpy as np, os
from datetime import date

DB_PATH = 'F:\\market_data.db'
OUT_DIR = 'out_data'
HOLD_DAYS = 60
STOP_LOSS = -20


def scan_once(sub):
    """对一只股票执行一次四象共振扫描（与扫描脚本完全一致）"""
    c = sub['close'].values.astype(float)
    v = sub['volume'].values.astype(float)
    dates = sub['date'].values

    close_s = pd.Series(c)
    ema12 = close_s.ewm(span=12).mean().values
    ema26 = close_s.ewm(span=26).mean().values
    dif = ema12 - ema26
    dea = pd.Series(dif).ewm(span=9).mean().values
    macd = 2 * (dif - dea)
    v60 = pd.Series(v).rolling(60).mean().values

    recent = 120
    if len(c) < recent:
        return None

    min_idx = np.argmin(c[-recent:]) + (len(c) - recent)
    if min_idx < 10:
        return None

    days_since = len(c) - 1 - min_idx
    if days_since < 15 or days_since > 30:
        return None

    ret_from_min = (c[-1] / c[min_idx] - 1) * 100
    if ret_from_min < 5 or ret_from_min > 50:
        return None

    ret_pre10 = (c[min_idx] / c[min_idx-10] - 1) * 100
    if ret_pre10 > -10 or ret_pre10 < -50:
        return None

    if macd[min_idx] >= -0.25:
        return None
    mw = macd[max(0, min_idx-5):min_idx+1]
    if len(mw) >= 3:
        if not (mw[-3] > mw[-2] > mw[-1]):
            return None
    else:
        return None

    if min_idx >= 5:
        pre5_v = np.mean(v[min_idx-5:min_idx])
        post5_v = np.mean(v[min_idx:min(min_idx+5, len(v))])
        vol_ratio = post5_v / max(pre5_v, 1)
    else:
        vol_ratio = 0
    if vol_ratio < 1.1:
        return None

    v60_val = v60[min_idx] if not np.isnan(v60[min_idx]) else np.mean(v[max(0, min_idx-60):min_idx])
    if v60_val <= 0:
        return None
    ws = max(0, min_idx - 30)
    we = min(len(v), min_idx + 5)
    vw = v[ws:we]
    vmi = np.argmin(vw) + ws
    if vmi - min_idx >= 0:
        return None
    v_min_ratio = v[vmi] / max(v60_val, 1)
    if v_min_ratio > 0.15:
        return None

    return {
        'code': sub['code'].iloc[0],
        'signal_date': dates[-1],
        'signal_price': round(c[-1], 2),
        'min_date': dates[min_idx],
        'min_price': round(c[min_idx], 2),
        'ret_from_min': round(ret_from_min, 1),
        'ret_pre10': round(ret_pre10, 1),
        'macd_col': round(macd[min_idx], 3),
        'vol_ratio': round(vol_ratio, 2),
        'v_min_ratio': round(v_min_ratio, 3),
        'days_since': days_since,
    }


def simulate_trade(sub_full, signal):
    """模拟信号出现后的60日交易"""
    sig_date = signal['signal_date']
    sig_price = signal['signal_price']
    code = signal['code']

    dates = sub_full['date'].values
    c = sub_full['close'].values.astype(float)

    # 找到信号日期在full数据中的位置
    try:
        buy_idx = list(dates).index(sig_date)
    except ValueError:
        return None

    buy_price = c[buy_idx]

    # 持有60日或止损
    sell_idx = None
    stop_triggered = False

    for i in range(buy_idx + 1, min(buy_idx + HOLD_DAYS + 1, len(c))):
        dd = (c[i] / buy_price - 1) * 100
        if dd < STOP_LOSS:
            sell_idx = i
            stop_triggered = True
            break

    if sell_idx is None:
        sell_idx = min(buy_idx + HOLD_DAYS, len(c) - 1)

    sell_price = c[sell_idx]
    sell_date = dates[sell_idx]
    pnl = (sell_price / buy_price - 1) * 100

    # 最大回撤
    hold_prices = c[buy_idx:sell_idx+1]
    if len(hold_prices) > 1:
        peak = np.maximum.accumulate(hold_prices)
        dd_arr = (hold_prices / peak - 1) * 100
        max_dd = round(dd_arr.min(), 1)
    else:
        max_dd = 0

    return {
        'code': code,
        'buy_date': sig_date,
        'buy_price': round(buy_price, 2),
        'sell_date': sell_date,
        'sell_price': round(sell_price, 2),
        'hold_days': sell_idx - buy_idx,
        'pnl_pct': round(pnl, 1),
        'max_dd': max_dd,
        'stop_triggered': stop_triggered,
        'min_date': signal['min_date'],
        'ret_from_min': signal['ret_from_min'],
        'ret_pre10': signal['ret_pre10'],
        'macd_col': signal['macd_col'],
        'vol_ratio': signal['vol_ratio'],
        'v_min_ratio': signal['v_min_ratio'],
    }


def backtest():
    conn = sqlite3.connect(DB_PATH)

    st_codes = set(r[0] for r in conn.execute("SELECT code FROM stock_st_status WHERE is_st=1").fetchall())
    codes = [r[0] for r in conn.execute(
        "SELECT DISTINCT code FROM daily_k WHERE code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%'"
    ).fetchall()]
    codes = [c for c in codes if c not in st_codes]

    # 获取所有历史月份（2024-01 到 2026-06）
    # 直接用SQL取每月最后交易日，避免全量日期
    month_ends = [r[0] for r in conn.execute(
        """SELECT MAX(date) FROM daily_k
            WHERE date >= '2024-01-01' AND date <= '2026-06-30'
            GROUP BY substr(date, 1, 7) ORDER BY date"""
    ).fetchall()]

    print(f'回测月份: {len(month_ends)}个 ({month_ends[0][:7]} ~ {month_ends[-1][:7]})')
    print(f'全市场非ST: {len(codes)}')
    print()

    all_trades = []

    for mi, me_date in enumerate(month_ends):
        # 跳过2026-07（数据可能不完整）
        if me_date >= '2026-07-01':
            continue
        print(f'\n[{mi+1}/{len(month_ends)}] 扫描 {me_date}...', end=' ', flush=True)
        me_signals = []
        for code in codes:
            try:
                sub = pd.read_sql(
                    "SELECT date, close, volume FROM daily_k WHERE code=? AND date <= ? ORDER BY date ASC",
                    conn, params=(code, me_date)
                )
                if len(sub) < 120:
                    continue
                sub['code'] = code
                sig = scan_once(sub)
                if sig:
                    me_signals.append(sig)
            except Exception:
                continue

        if not me_signals:
            print('无信号')
            continue

        print(f'{len(me_signals)}个信号')

        # 对每个信号模拟交易
        for sig in me_signals:
            # 获取完整数据用于模拟
            sub_full = pd.read_sql(
                "SELECT date, close, volume FROM daily_k WHERE code=? ORDER BY date ASC",
                conn, params=(sig['code'],)
            )
            if len(sub_full) < 200:
                continue
            sub_full['code'] = sig['code']

            trade = simulate_trade(sub_full, sig)
            if trade:
                all_trades.append(trade)

        print(f'  {me_date}: {len(me_signals)}个信号')

    conn.close()
    return all_trades


def output(trades):
    if not trades:
        print('无交易')
        return

    df = pd.DataFrame(trades)

    # 去重：同股票60日内只保留第一笔
    df = df.sort_values(['code', 'buy_date'])
    df['prev_buy'] = df.groupby('code')['buy_date'].shift()
    df['days_since_prev'] = (pd.to_datetime(df['buy_date']) - pd.to_datetime(df['prev_buy'])).dt.days
    df = df[df['days_since_prev'].fillna(999) >= 60].reset_index(drop=True)

    total = len(df)
    wins = df[df['pnl_pct'] > 0]
    losses = df[df['pnl_pct'] <= 0]

    win_rate = len(wins) / total * 100
    avg_pnl = df['pnl_pct'].mean()
    med_pnl = df['pnl_pct'].median()

    df['cumulative'] = (1 + df['pnl_pct'] / 100).cumprod()
    total_return = (df['cumulative'].iloc[-1] - 1) * 100

    max_consec_loss = 0
    cur = 0
    for v in df['pnl_pct'] <= 0:
        if v:
            cur += 1
            if cur > max_consec_loss: max_consec_loss = cur
        else:
            cur = 0

    print()
    print('=' * 65)
    print('四象共振 · 底部反转回测 v4')
    print(f'方法: 每月末全市场扫描，买入持有{HOLD_DAYS}日')
    print(f'止损: {STOP_LOSS}%')
    print(f'回测: 2024-01 ~ 2026-06')
    print('=' * 65)
    print(f'总交易次数: {total}')
    print(f'胜率: {win_rate:.1f}%')
    print(f'平均收益率: {avg_pnl:.1f}%')
    print(f'中位数收益率: {med_pnl:.1f}%')
    print(f'累计收益率(等权): {total_return:.1f}%')
    print(f'最大连续亏损: {max_consec_loss}次')
    print(f'止损触发: {df["stop_triggered"].sum()}/{total} ({df["stop_triggered"].sum()/total*100:.1f}%)')
    print()

    ranges = [
        ('> 30%', df[df['pnl_pct'] > 30]),
        ('15~30%', df[(df['pnl_pct'] > 15) & (df['pnl_pct'] <= 30)]),
        ('5~15%', df[(df['pnl_pct'] > 5) & (df['pnl_pct'] <= 15)]),
        ('0~5%', df[(df['pnl_pct'] > 0) & (df['pnl_pct'] <= 5)]),
        ('-5~0%', df[(df['pnl_pct'] > -5) & (df['pnl_pct'] <= 0)]),
        ('-15~-5%', df[(df['pnl_pct'] > -15) & (df['pnl_pct'] <= -5)]),
        ('<-15%', df[df['pnl_pct'] <= -15]),
    ]
    for label, grp in ranges:
        cnt = len(grp)
        pct = cnt / total * 100
        bar = '█' * int(pct / 2)
        print(f'  {label:>8}: {cnt:>4}次 ({pct:5.1f}%) {bar}')

    print()
    print('Top 10盈利:')
    for _, r in df.nlargest(10, 'pnl_pct').iterrows():
        print(f'  {r["code"]} {r["buy_date"]} 买{r["buy_price"]} 卖{r["sell_price"]}  +{r["pnl_pct"]}%')

    print('\nTop 10亏损:')
    for _, r in df.nsmallest(10, 'pnl_pct').iterrows():
        print(f'  {r["code"]} {r["buy_date"]} 买{r["buy_price"]} 卖{r["sell_price"]}  {r["pnl_pct"]}%')

    # 文件
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, 'si_xiang_backtest_v4.md')
    lines = ['# 四象共振 · 底部反转回测 v4',
             f'方法: 每月末全市场扫描，买入持有{HOLD_DAYS}日',
             f'止损: {STOP_LOSS}%',
             f'回测: 2024-01 ~ 2026-06',
             f'总交易次数: {total}',
             '', '## 总统计',
             f'- 胜率: {win_rate:.1f}%',
             f'- 平均收益率: {avg_pnl:.1f}%',
             f'- 中位数收益率: {med_pnl:.1f}%',
             f'- 累计收益率(等权): {total_return:.1f}%',
             f'- 最大连续亏损: {max_consec_loss}次',
             f'- 止损触发: {df["stop_triggered"].sum()}次 ({df["stop_triggered"].sum()/total*100:.1f}%)',
             '', '## 收益率分布']
    for label, grp in ranges:
        lines.append(f'- {label}: {len(grp)}次 ({len(grp)/total*100:.1f}%)')
    lines.append('')
    lines.append('## Top 30盈利')
    lines.append('| 代码 | 买入日 | 买入价 | 卖出日 | 卖出价 | 收益% | 回撤% | 止损 |')
    lines.append('|------|--------|--------|--------|--------|-------|------|------|')
    for _, r in df.nlargest(30, 'pnl_pct').iterrows():
        lines.append(f"| {r['code']} | {r['buy_date']} | {r['buy_price']} | {r['sell_date']} | {r['sell_price']} | {r['pnl_pct']} | {r['max_dd']} | {'是' if r['stop_triggered'] else '否'} |")
    lines.append('')
    lines.append('## Top 30亏损')
    lines.append('| 代码 | 买入日 | 买入价 | 卖出日 | 卖出价 | 收益% | 回撤% | 止损 |')
    lines.append('|------|--------|--------|--------|--------|-------|------|------|')
    for _, r in df.nsmallest(30, 'pnl_pct').iterrows():
        lines.append(f"| {r['code']} | {r['buy_date']} | {r['buy_price']} | {r['sell_date']} | {r['sell_price']} | {r['pnl_pct']} | {r['max_dd']} | {'是' if r['stop_triggered'] else '否'} |")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'\n报告: {out_path}')


if __name__ == '__main__':
    import time
    t0 = time.time()
    trades = backtest()
    output(trades)
    print(f'\n耗时: {time.time() - t0:.0f}秒')