# -*- coding: utf-8 -*-
"""
抖音形态回测 - 倍量过左峰
4个条件：
1. 左峰放倍量（成交量>=2倍近20日均量，且为近期最高量）
2. 左峰后缩量调整，不破倍量阳线低点
3. 调整时间5-20天
4. 突破左峰时必须是倍量大阳线（涨幅>3%，量>=2倍均量），量能不能超过第一根倍量

买入：突破日尾盘
止损：倍量阳线低点
持有：20个交易日
"""
import sqlite3, pandas as pd, numpy as np, os, sys
from datetime import date

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = 'F:\\market_data.db'
OUT_DIR = 'out_data'
HOLD_DAYS = 20
STOP_LOSS_PCT = -8  # 跌破倍量阳线低点止损


def scan_double_volume_peak(sub):
    """扫描倍量过左峰形态"""
    c = pd.to_numeric(sub['close'], errors='coerce').values
    o = pd.to_numeric(sub['open'], errors='coerce').values
    v = pd.to_numeric(sub['volume'], errors='coerce').fillna(0).values
    dates = sub['date'].values
    high = pd.to_numeric(sub['high'], errors='coerce').values
    low = pd.to_numeric(sub['low'], errors='coerce').values

    # 清理NaN
    mask = ~(np.isnan(c) | np.isnan(o) | np.isnan(v) | np.isnan(high) | np.isnan(low))
    c, o, v, high, low, dates = c[mask], o[mask], v[mask], high[mask], low[mask], dates[mask]

    if len(c) < 60:
        return []

    signals = []

    # 从第40根K线开始扫描，留足前后空间
    for i in range(40, len(c) - 5):
        # === 条件1: 左峰放倍量 ===
        # 近20日均量
        vol_ma20 = np.mean(v[max(0, i-20):i])
        if vol_ma20 <= 0:
            continue

        # 当日量能 >= 2倍均量
        if v[i] < vol_ma20 * 2:
            continue

        # 当日为近期最高量（20日内）
        recent_vol = v[max(0, i-20):i+1]
        if v[i] < np.max(recent_vol) * 0.95:  # 允许5%误差
            continue

        # 当日为阳线
        if c[i] <= o[i]:
            continue

        peak_price = high[i]  # 左峰最高价
        peak_vol = v[i]  # 左峰量能
        peak_low = low[i]  # 倍量阳线低点

        # === 条件2: 缩量调整，不破倍量阳线低点 ===
        # 条件3: 调整时间5-20天
        for adjust_days in range(5, 21):
            j = i + adjust_days
            if j >= len(c):
                break

            # 检查调整期间
            adjust_vols = v[i+1:j]
            adjust_lows = low[i+1:j]
            adjust_closes = c[i+1:j]

            if len(adjust_lows) < adjust_days - 1:
                continue

            # 调整期间不破倍量阳线低点
            if np.min(adjust_lows) < peak_low:
                break  # 跌破了，不符合

            # 调整期间缩量（均量 < 峰值量的50%）
            adjust_avg_vol = np.mean(adjust_vols)
            if adjust_avg_vol > peak_vol * 0.6:
                continue  # 没有缩量

            # === 条件4: 突破左峰时倍量大阳线 ===
            # 突破日
            breakout_day = j
            if breakout_day >= len(c):
                break

            # 突破日收盘价 > 左峰最高价
            if c[breakout_day] <= peak_price:
                continue

            # 突破日涨幅 > 3%
            chg_pct = (c[breakout_day] - o[breakout_day]) / o[breakout_day] * 100
            if chg_pct < 3:
                continue

            # 突破日量能 >= 2倍均量
            vol_ma_before = np.mean(v[max(0, breakout_day-20):breakout_day])
            if vol_ma_before <= 0:
                continue
            if v[breakout_day] < vol_ma_before * 2:
                continue

            # 突破日量能不能超过第一根倍量
            if v[breakout_day] > peak_vol:
                continue

            signals.append({
                'code': sub['code'].iloc[0],
                'peak_date': dates[i],
                'peak_price': round(peak_price, 2),
                'peak_vol': int(peak_vol),
                'peak_low': round(peak_low, 2),
                'adjust_days': adjust_days,
                'breakout_date': dates[breakout_day],
                'breakout_price': round(c[breakout_day], 2),
                'breakout_chg': round(chg_pct, 2),
                'breakout_vol': int(v[breakout_day]),
                'vol_ratio_peak': round(v[breakout_day] / peak_vol, 2),
            })
            break  # 找到第一个突破就跳出调整天数循环

    return signals


def simulate_trade(sub_full, signal):
    """模拟信号出现后的20日交易"""
    breakout_date = signal['breakout_date']
    buy_price = signal['breakout_price']
    stop_price = signal['peak_low']  # 止损位=倍量阳线低点

    dates = sub_full['date'].values
    c = sub_full['close'].values.astype(float)
    lows = sub_full['low'].values.astype(float)

    try:
        buy_idx = list(dates).index(breakout_date)
    except ValueError:
        return None

    sell_idx = None
    stop_triggered = False

    for k in range(buy_idx + 1, min(buy_idx + HOLD_DAYS + 1, len(c))):
        # 止损：跌破倍量阳线低点
        if lows[k] < stop_price:
            sell_idx = k
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
        peak_arr = np.maximum.accumulate(hold_prices)
        dd_arr = (hold_prices / peak_arr - 1) * 100
        max_dd = round(dd_arr.min(), 1)
    else:
        max_dd = 0

    return {
        **signal,
        'buy_price': buy_price,
        'sell_date': sell_date,
        'sell_price': round(sell_price, 2),
        'hold_days': sell_idx - buy_idx,
        'pnl_pct': round(pnl, 1),
        'max_dd': max_dd,
        'stop_triggered': stop_triggered,
    }


def backtest():
    conn = sqlite3.connect(DB_PATH)

    # 获取非ST、非北交所股票
    try:
        st_codes = set(r[0] for r in conn.execute(
            "SELECT code FROM stock_st_status WHERE is_st=1"
        ).fetchall())
    except:
        st_codes = set()

    codes = [r[0] for r in conn.execute(
        "SELECT DISTINCT code FROM daily_k WHERE code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%'"
    ).fetchall()]
    codes = [c for c in codes if c not in st_codes]

    # 回测区间 2024-01 到 2026-06
    print(f'倍量过左峰 回测 | 股票数: {len(codes)} | 区间: 2024-01 ~ 2026-06')

    all_trades = []

    for ci, code in enumerate(codes):
        if ci % 500 == 0:
            print(f'  [{ci}/{len(codes)}] {code}...', flush=True)

        try:
            sub = pd.read_sql(
                "SELECT date, open, high, low, close, volume FROM daily_k "
                "WHERE code=? AND date >= '2023-06-01' AND date <= '2026-06-30' ORDER BY date ASC",
                conn, params=(code,)
            )
        except:
            continue

        if len(sub) < 60:
            continue

        sub['code'] = code

        # 扫描信号
        sigs = scan_double_volume_peak(sub)
        if not sigs:
            continue

        # 模拟交易
        for sig in sigs:
            sub_full = pd.read_sql(
                "SELECT date, open, high, low, close, volume FROM daily_k "
                "WHERE code=? ORDER BY date ASC",
                conn, params=(code,)
            )
            if len(sub_full) < 60:
                continue
            sub_full['code'] = code

            trade = simulate_trade(sub_full, sig)
            if trade:
                all_trades.append(trade)

    conn.close()
    return all_trades


def output(trades):
    if not trades:
        print('无交易')
        return

    df = pd.DataFrame(trades)

    # 去重：同股票30日内只保留第一笔
    df = df.sort_values(['code', 'breakout_date'])
    df['prev_breakout'] = df.groupby('code')['breakout_date'].shift()
    df['days_since_prev'] = (pd.to_datetime(df['breakout_date']) - pd.to_datetime(df['prev_breakout'])).dt.days
    df = df[df['days_since_prev'].fillna(999) >= 30].reset_index(drop=True)

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
            if cur > max_consec_loss:
                max_consec_loss = cur
        else:
            cur = 0

    print()
    print('=' * 65)
    print('倍量过左峰 · 回测')
    print(f'买入: 突破日收盘 | 止损: 倍量阳线低点 | 持有: {HOLD_DAYS}日')
    print(f'回测: 2024-01 ~ 2026-06')
    print('=' * 65)
    print(f'总交易次数: {total}')
    print(f'胜率: {win_rate:.1f}%')
    print(f'平均收益率: {avg_pnl:.1f}%')
    print(f'中位数收益率: {med_pnl:.1f}%')
    print(f'累计收益率(等权): {total_return:.1f}%')
    print(f'最大连续亏损: {max_consec_loss}次')
    print(f'止损触发: {df["stop_triggered"].sum()}/{total} ({df["stop_triggered"].sum()/total*100:.1f}%)')
    print(f'平均调整天数: {df["adjust_days"].mean():.1f}日')
    print(f'平均突破涨幅: {df["breakout_chg"].mean():.1f}%')

    ranges = [
        ('> 20%', df[df['pnl_pct'] > 20]),
        ('10~20%', df[(df['pnl_pct'] > 10) & (df['pnl_pct'] <= 20)]),
        ('5~10%', df[(df['pnl_pct'] > 5) & (df['pnl_pct'] <= 10)]),
        ('0~5%', df[(df['pnl_pct'] > 0) & (df['pnl_pct'] <= 5)]),
        ('-5~0%', df[(df['pnl_pct'] > -5) & (df['pnl_pct'] <= 0)]),
        ('-10~-5%', df[(df['pnl_pct'] > -10) & (df['pnl_pct'] <= -5)]),
        ('<-10%', df[df['pnl_pct'] <= -10]),
    ]
    for label, grp in ranges:
        cnt = len(grp)
        pct = cnt / total * 100
        bar = '█' * int(pct / 2)
        print(f'  {label:>8}: {cnt:>4}次 ({pct:5.1f}%) {bar}')

    print()
    print('Top 15盈利:')
    for _, r in df.nlargest(15, 'pnl_pct').iterrows():
        print(f'  {r["code"]} {r["breakout_date"]} 买{r["buy_price"]} 卖{r["sell_price"]} +{r["pnl_pct"]}% 调整{r["adjust_days"]}日')

    print('\nTop 15亏损:')
    for _, r in df.nsmallest(15, 'pnl_pct').iterrows():
        print(f'  {r["code"]} {r["breakout_date"]} 买{r["buy_price"]} 卖{r["sell_price"]} {r["pnl_pct"]}% 调整{r["adjust_days"]}日')

    # 按年份统计
    df['year'] = df['breakout_date'].str[:4]
    print('\n按年份:')
    for year, grp in df.groupby('year'):
        yr_total = len(grp)
        yr_win = len(grp[grp['pnl_pct'] > 0])
        yr_avg = grp['pnl_pct'].mean()
        print(f'  {year}: {yr_total}次 胜率{yr_win/yr_total*100:.1f}% 均收益{yr_avg:.1f}%')

    # 保存报告
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, 'douyin_backtest_倍量过左峰.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f'# 倍量过左峰 · 回测\n\n')
        f.write(f'**来源**: 抖音"宝哥论谷"倍量过左峰战法\n\n')
        f.write(f'## 条件\n')
        f.write(f'1. 左峰放倍量（≥2倍20日均量，近期最高量）\n')
        f.write(f'2. 缩量调整，不破倍量阳线低点\n')
        f.write(f'3. 调整5-20天\n')
        f.write(f'4. 突破左峰为倍量大阳线(涨>3%)，量不超过第一根倍量\n\n')
        f.write(f'## 统计\n\n')
        f.write(f'| 指标 | 值 |\n|------|------|\n')
        f.write(f'| 总交易 | {total} |\n')
        f.write(f'| 胜率 | {win_rate:.1f}% |\n')
        f.write(f'| 平均收益 | {avg_pnl:.1f}% |\n')
        f.write(f'| 中位收益 | {med_pnl:.1f}% |\n')
        f.write(f'| 累计收益(等权) | {total_return:.1f}% |\n')
        f.write(f'| 最大连亏 | {max_consec_loss}次 |\n')
        f.write(f'| 止损触发 | {df["stop_triggered"].sum()}/{total} |\n')
        f.write(f'| 平均调整天数 | {df["adjust_days"].mean():.1f}日 |\n\n')

        f.write(f'## 收益分布\n\n')
        for label, grp in ranges:
            f.write(f'- {label}: {len(grp)}次 ({len(grp)/total*100:.1f}%)\n')

        f.write(f'\n## Top 30交易\n\n')
        f.write(f'| 代码 | 突破日 | 买入 | 卖出日 | 卖出 | 收益% | 回撤% | 调整天 | 止损 |\n')
        f.write(f'|------|--------|------|--------|------|-------|------|--------|------|\n')
        for _, r in df.nlargest(30, 'pnl_pct').iterrows():
            f.write(f'| {r["code"]} | {r["breakout_date"]} | {r["buy_price"]} | {r["sell_date"]} | {r["sell_price"]} | +{r["pnl_pct"]}% | {r["max_dd"]}% | {r["adjust_days"]} | {"是" if r["stop_triggered"] else "否"} |\n')

    print(f'\n报告: {out_path}')
    return df


if __name__ == '__main__':
    import time
    t0 = time.time()
    trades = backtest()
    df = output(trades)
    print(f'\n耗时: {time.time() - t0:.0f}秒')
