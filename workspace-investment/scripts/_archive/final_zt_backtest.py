# -*- coding: utf-8 -*-
"""
最终版回测：优化后的涨停确认信号
==================================
条件：
1. 涨停次日缩量（量 < 涨停日量 * 0.5）
2. 不破底（次日最低价 >= 涨停最低价 * 0.995）
3. 价格过滤：涨停价 >= 10元（剔除低价股）

对比基准：全部涨停次日开盘买入持5日
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import sqlite3, statistics, json

db = sqlite3.connect('F:/market_data.db')
cur = db.cursor()

# 获取涨停数据
zt_rows = cur.execute("""
    SELECT z.id, z.code, z.trade_date, z.close_price as zt_close, z.zt_type
    FROM daily_zt z WHERE z.trade_date >= '2026-01-01'
    ORDER BY z.trade_date
""").fetchall()

print(f'涨停记录: {len(zt_rows)}条')

# 回测：优化策略
opt_results = []
for z in zt_rows:
    code, zt_date, zt_close, zt_type = z[1], z[2], z[3], z[4]
    
    # 价格过滤
    if zt_close < 10:
        continue
    
    # 涨停日K线（最低价、成交量）
    zt_k = cur.execute("SELECT low, volume FROM daily_k WHERE code=? AND date=?", (code, zt_date)).fetchone()
    if not zt_k:
        continue
    zt_low, zt_vol = zt_k
    
    # 次日K线
    next_k = cur.execute("""
        SELECT date, open, close, low, volume FROM daily_k 
        WHERE code=? AND date>? ORDER BY date LIMIT 1
    """, (code, zt_date)).fetchone()
    if not next_k:
        continue
    next_date, next_open, next_close, next_low, next_vol = next_k
    next_vol = float(next_vol) if next_vol else 0
    zt_vol = float(zt_vol) if zt_vol else 0
    
    # 条件1：缩量（量 < 涨停量 * 0.5）
    if zt_vol > 0 and next_vol >= zt_vol * 0.5:
        continue
    
    # 条件2：不破底
    if next_low < zt_low * 0.995:
        continue
    
    # 买入：次日开盘
    buy_price = next_open
    
    # 持有5个交易日
    future = cur.execute("""
        SELECT date, close FROM daily_k 
        WHERE code=? AND date>? ORDER BY date LIMIT 5
    """, (code, next_date)).fetchall()
    
    if len(future) < 3:
        continue
    
    sell_price = future[min(4, len(future)-1)][1]
    chg = (sell_price - buy_price) / buy_price * 100
    
    opt_results.append({
        'code': code, 'zt_date': zt_date, 'buy_date': next_date,
        'buy_price': buy_price, 'sell_price': sell_price,
        'chg': round(chg, 2), 'vol_ratio': round(next_vol/zt_vol, 2) if zt_vol > 0 else 0,
        'low_ratio': round(next_low/zt_low, 3) if zt_low > 0 else 0,
        'type': zt_type, 'zt_close': zt_close,
    })

print(f'优化策略触发: {len(opt_results)}次')

# 统计
opt_chgs = [r['chg'] for r in opt_results]
opt_wins = [c for c in opt_chgs if c > 0]
opt_losses = [c for c in opt_chgs if c <= 0]

print(f'胜率: {len(opt_wins)/len(opt_chgs)*100:.1f}%' if opt_chgs else '无数据')
print(f'平均收益: {statistics.mean(opt_chgs):+.2f}%' if opt_chgs else '无数据')
print(f'中位数: {statistics.median(opt_chgs):+.2f}%' if opt_chgs else '无数据')
print(f'最大收益: {max(opt_chgs):+.2f}%' if opt_chgs else '无数据')
print(f'最大亏损: {min(opt_chgs):+.2f}%' if opt_chgs else '无数据')
if opt_wins and opt_losses:
    print(f'盈亏比: {abs(statistics.mean(opt_wins))/abs(statistics.mean(opt_losses)):.2f}')

# 月度
print()
print('月度表现:')
monthly = {}
for r in opt_results:
    m = r['zt_date'][:7]
    if m not in monthly: monthly[m] = []
    monthly[m].append(r['chg'])
for m in sorted(monthly.keys()):
    c = monthly[m]; w = [x for x in c if x > 0]
    print(f'  {m}: 触发{len(c)}次 胜率{len(w)/len(c)*100:.0f}% 收益{statistics.mean(c):+.2f}%')

# 基准
print()
print('基准（全部涨停次日开盘买入持5日）:')
benchmark = []
for zt_date in sorted(set(z[2] for z in zt_rows)):
    next_date = cur.execute("SELECT MIN(date) FROM daily_k WHERE date>?", (zt_date,)).fetchone()[0]
    if not next_date: continue
    rows = cur.execute("""
        SELECT z.code, k.open FROM daily_zt z
        JOIN daily_k k ON z.code=k.code AND k.date=?
        WHERE z.trade_date=?
    """, (next_date, zt_date)).fetchall()
    for code, buy_price in rows:
        future = cur.execute("SELECT close FROM daily_k WHERE code=? AND date>? ORDER BY date LIMIT 5", (code, next_date)).fetchall()
        if len(future) >= 3:
            chg = (future[min(4,len(future)-1)][0] - buy_price) / buy_price * 100
            benchmark.append(chg)

bm_wins = [c for c in benchmark if c > 0]
print(f'总样本: {len(benchmark)}次 胜率{len(bm_wins)/len(benchmark)*100:.1f}% 收益{statistics.mean(benchmark):+.2f}%')

# 最终对比
print()
print('=' * 60)
print('最终对比')
print('=' * 60)
print(f'{"策略":<35} {"触发":<8} {"胜率":<10} {"收益":<12} {"中位数":<10}')
print('-' * 60)
print(f'{"优化策略(量<0.5+不破底+价>=10)":<35} {len(opt_chgs):<8} {len(opt_wins)/len(opt_chgs)*100 if opt_chgs else 0:<10.1f}% {statistics.mean(opt_chgs) if opt_chgs else 0:<+12.2f}% {statistics.median(opt_chgs) if opt_chgs else 0:<+10.2f}%')
print(f'{"全部涨停(基准)":<35} {len(benchmark):<8} {len(bm_wins)/len(benchmark)*100:<10.1f}% {statistics.mean(benchmark):<+12.2f}% {statistics.median(benchmark):<+10.2f}%')

improvement = statistics.mean(opt_chgs) - statistics.mean(benchmark) if opt_chgs else 0
print(f'\n提升: {improvement:+.2f}%')
print(f'结论: {"✅ 优化策略显著优于基准" if improvement > 0 else "❌ 仍需改进"}')

# 保存
with open('out_data/zt_signal_optimized_backtest.json', 'w', encoding='utf-8') as f:
    json.dump({'results': opt_results, 'summary': {'total': len(opt_chgs), 'win_rate': round(len(opt_wins)/len(opt_chgs)*100,1) if opt_chgs else 0, 'avg_return': round(statistics.mean(opt_chgs),2) if opt_chgs else 0, 'benchmark_avg': round(statistics.mean(benchmark),2)}}, f, ensure_ascii=False, indent=2)

db.close()