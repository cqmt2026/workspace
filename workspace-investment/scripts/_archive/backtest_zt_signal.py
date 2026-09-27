# -*- coding: utf-8 -*-
"""
历史回测：涨停确认信号在signal_aggregator中的效果
============================================
模拟2026年1月~7月，每天运行signal_aggregator，统计：
1. 每天触发了几只涨停确认信号
2. 触发后5日收益如何
3. 对比无脑打板的收益
4. 缩量+不破底 vs 其他组合的效果
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from scripts.signal_aggregator import SignalAggregator
import sqlite3
from datetime import datetime, timedelta
import statistics, json

WORK_DIR = '.'
OUT_DIR = 'out_data'

# 获取所有有涨停+次日K线的日期对
db = sqlite3.connect('F:/market_data.db')
cur = db.cursor()

# 获取所有涨停日期
zt_dates = [r[0] for r in cur.execute(
    "SELECT DISTINCT trade_date FROM daily_zt WHERE trade_date >= '2026-01-01' ORDER BY trade_date"
).fetchall()]
print(f'涨停交易日: {len(zt_dates)}天')

# 对每个涨停日期，找下一个交易日
date_pairs = []
for zt_date in zt_dates:
    next_date = cur.execute(
        "SELECT MIN(date) FROM daily_k WHERE date>?", (zt_date,)
    ).fetchone()[0]
    if next_date:
        date_pairs.append((zt_date, next_date))

print(f'有完整数据的日期对: {len(date_pairs)}对')
print()

# ===== 批量回测 =====
all_results = []
agg = SignalAggregator()

for zt_date, next_date in date_pairs:
    # 加载涨停确认信号（用next_date作为参数）
    sigs = agg.load_zt_confirmation_signals(next_date)
    if not sigs:
        continue
    
    # 分类
    passed = {k:v for k,v in sigs.items() if v['zt_score'] >= 100}
    failed = {k:v for k,v in sigs.items() if v['zt_score'] < 100}
    break_failed = {k:v for k,v in sigs.items() if '破底' in v['zt_detail']}
    
    # 统计通过票的后续5日收益
    for code, info in passed.items():
        # 买入：次日(next_date)开盘
        buy_k = cur.execute(
            "SELECT open, close FROM daily_k WHERE code=? AND date=?", 
            (code, next_date)
        ).fetchone()
        if not buy_k:
            continue
        buy_price = buy_k[0]  # 开盘买入
        
        # 持有5个交易日
        future = cur.execute("""
            SELECT date, close FROM daily_k 
            WHERE code=? AND date>? ORDER BY date LIMIT 5
        """, (code, next_date)).fetchall()
        
        if len(future) >= 3:
            sell_price = future[min(4, len(future)-1)][1]
            chg = (sell_price - buy_price) / buy_price * 100
            
            # 每日最高收益（途中最高点）
            max_chg = 0
            for f in future:
                f_chg = (f[1] - buy_price) / buy_price * 100
                max_chg = max(max_chg, f_chg)
            
            all_results.append({
                'code': code,
                'zt_date': zt_date,
                'buy_date': next_date,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'chg': round(chg, 2),
                'max_chg': round(max_chg, 2),
                'vol_ratio': info['zt_vol_ratio'],
                'low_ratio': info['zt_low_ratio'],
                'type': info.get('zt_type', ''),
            })

print(f'历史回测完成，共触发 {len(all_results)} 次交易信号')
print()

# ===== 统计分析 =====
if all_results:
    chgs = [r['chg'] for r in all_results]
    wins = [c for c in chgs if c > 0]
    losses = [c for c in chgs if c <= 0]
    
    print('=' * 60)
    print('信号效果统计')
    print('=' * 60)
    print(f'总触发: {len(chgs)}次')
    print(f'胜率: {len(wins)/len(chgs)*100:.1f}%')
    print(f'平均收益: {statistics.mean(chgs):.2f}%')
    print(f'中位数收益: {statistics.median(chgs):.2f}%')
    print(f'最大收益: {max(chgs):.2f}%')
    print(f'最大亏损: {min(chgs):.2f}%')
    if wins and losses:
        print(f'平均赢: {statistics.mean(wins):.2f}%')
        print(f'平均亏: {statistics.mean(losses):.2f}%')
        print(f'盈亏比: {abs(statistics.mean(wins))/abs(statistics.mean(losses)):.2f}')
    
    # 分月度
    print()
    print('=' * 60)
    print('月度表现')
    print('=' * 60)
    monthly = {}
    for r in all_results:
        m = r['zt_date'][:7]
        if m not in monthly:
            monthly[m] = []
        monthly[m].append(r['chg'])
    
    for m in sorted(monthly.keys()):
        chgs_m = monthly[m]
        wins_m = [c for c in chgs_m if c > 0]
        print(f'  {m}: 触发{len(chgs_m)}次 胜率{len(wins_m)/len(chgs_m)*100:.0f}% 收益{statistics.mean(chgs_m):+.2f}%')
    
    # Top 10 最佳交易
    print()
    print('=' * 60)
    print('最佳10笔交易')
    print('=' * 60)
    for r in sorted(all_results, key=lambda x: x['chg'], reverse=True)[:10]:
        print(f"  {r['zt_date']} {r['code']}: 买入{r['buy_price']:.2f} → 卖出{r['sell_price']:.2f} ({r['chg']:+.2f}%)")
    
    # Worst 10
    print()
    print('最差10笔交易')
    for r in sorted(all_results, key=lambda x: x['chg'])[:10]:
        print(f"  {r['zt_date']} {r['code']}: 买入{r['buy_price']:.2f} → 卖出{r['sell_price']:.2f} ({r['chg']:+.2f}%)")

# ===== 对比基准 =====
print()
print('=' * 60)
print('对比基准：全部涨停次日开盘买入持5日')
print('=' * 60)

# 基准
benchmark = []
for zt_date, next_date in date_pairs:
    rows = cur.execute("""
        SELECT z.code, k.open
        FROM daily_zt z
        JOIN daily_k k ON z.code=k.code AND k.date=?
        WHERE z.trade_date=?
    """, (next_date, zt_date)).fetchall()
    
    for code, buy_price in rows:
        future = cur.execute("""
            SELECT close FROM daily_k 
            WHERE code=? AND date>? ORDER BY date LIMIT 5
        """, (code, next_date)).fetchall()
        
        if len(future) >= 3:
            sell_price = future[min(4, len(future)-1)][0]
            chg = (sell_price - buy_price) / buy_price * 100
            benchmark.append(chg)

if benchmark:
    bm_wins = [c for c in benchmark if c > 0]
    print(f'总样本: {len(benchmark)}次')
    print(f'胜率: {len(bm_wins)/len(benchmark)*100:.1f}%')
    print(f'平均收益: {statistics.mean(benchmark):.2f}%')
    print(f'中位数: {statistics.median(benchmark):.2f}%')

# ===== 汇总 =====
print()
print('=' * 60)
print('最终对比')
print('=' * 60)
if all_results and benchmark:
    print(f'{"策略":<30} {"触发":<8} {"胜率":<10} {"平均收益":<12} {"中位数":<10}')
    print('-' * 60)
    print(f'{"涨停确认信号(缩量+不破底)":<30} {len(chgs):<8} {len(wins)/len(chgs)*100:<10.1f}% {statistics.mean(chgs):<12.2f}% {statistics.median(chgs):<10.2f}%')
    print(f'{"全部涨停(无脑打板基准)":<30} {len(benchmark):<8} {len(bm_wins)/len(benchmark)*100:<10.1f}% {statistics.mean(benchmark):<12.2f}% {statistics.median(benchmark):<10.2f}%')
    
    improvement = (statistics.mean(chgs) - statistics.mean(benchmark))
    print(f'\n策略提升: {improvement:+.2f}%')
    print(f'结论: {"✅ 策略显著优于基准" if improvement > 0 else "❌ 策略不如基准"}')

# 保存结果
output = {
    'signal_results': all_results,
    'summary': {
        'total_signals': len(all_results) if all_results else 0,
        'win_rate': round(len(wins)/len(chgs)*100, 1) if all_results and chgs else 0,
        'avg_return': round(statistics.mean(chgs), 2) if all_results else 0,
        'benchmark_avg': round(statistics.mean(benchmark), 2) if benchmark else 0,
    }
}
with open(f'{OUT_DIR}/zt_signal_backtest_results.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f'\n结果已保存: {OUT_DIR}/zt_signal_backtest_results.json')

agg.close()
db.close()