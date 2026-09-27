# -*- coding: utf-8 -*-
"""
优化版：加入价格+流动性过滤后重新回测
=================================
发现：
1. 0-10元低价股胜率仅21%，收益-7.51% → 剔除
2. 量比<0.05的极度缩量不是好事 → 流动性枯竭 → 剔除
3. 价比较大（>1.03）的胜率低 → 说明回踩太深不好

优化方案：
- 买入价 >= 10元（剔除垃圾低价股）
- 量比 > 0.05（剔除流动性枯竭）
- 价比 <= 1.03（回踩不能太深）
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import sqlite3, json, statistics

db = sqlite3.connect('F:/market_data.db')
cur = db.cursor()

with open('out_data/zt_signal_backtest_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data['signal_results']

# ===== 原策略 =====
all_chgs = [r['chg'] for r in results]
all_wins = [c for c in all_chgs if c > 0]
print('原策略（缩量<0.7+不破底）:')
print(f'  触发{len(all_chgs)}次 胜率{len(all_wins)/len(all_chgs)*100:.1f}% 收益{statistics.mean(all_chgs):+.2f}%')
print()

# ===== 方案A：只剔除低价股（<10元） =====
a = [r for r in results if r['buy_price'] >= 10]
a_chgs = [r['chg'] for r in a]
a_wins = [c for c in a_chgs if c > 0]
print('方案A：剔除<10元低价股:')
print(f'  触发{len(a_chgs)}次 胜率{len(a_wins)/len(a_chgs)*100:.1f}% 收益{statistics.mean(a_chgs):+.2f}%')

# ===== 方案B：剔除流动性枯竭（量比<0.05） =====
b = [r for r in results if r['vol_ratio'] >= 0.05]
b_chgs = [r['chg'] for r in b]
b_wins = [c for c in b_chgs if c > 0]
print('\n方案B：剔除量比<0.05（流动性枯竭）:')
print(f'  触发{len(b_chgs)}次 胜率{len(b_wins)/len(b_chgs)*100:.1f}% 收益{statistics.mean(b_chgs):+.2f}%')

# ===== 方案C：回踩不能太深（价比<=1.03） =====
c = [r for r in results if r['low_ratio'] <= 1.03]
c_chgs = [r['chg'] for r in c]
c_wins = [c2 for c2 in c_chgs if c2 > 0]
print('\n方案C：回踩不深（价比<=1.03）:')
print(f'  触发{len(c_chgs)}次 胜率{len(c_wins)/len(c_chgs)*100:.1f}% 收益{statistics.mean(c_chgs):+.2f}%')

# ===== 方案D：价格>=10 + 量比>=0.05 =====
d = [r for r in results if r['buy_price'] >= 10 and r['vol_ratio'] >= 0.05]
d_chgs = [r['chg'] for r in d]
d_wins = [c3 for c3 in d_chgs if c3 > 0]
print('\n方案D：价格>=10 + 量比>=0.05:')
print(f'  触发{len(d_chgs)}次 胜率{len(d_wins)/len(d_chgs)*100:.1f}% 收益{statistics.mean(d_chgs):+.2f}%')

# ===== 方案E：价格>=10 + 量比>=0.05 + 价比<=1.03 =====
e = [r for r in results if r['buy_price'] >= 10 and r['vol_ratio'] >= 0.05 and r['low_ratio'] <= 1.03]
e_chgs = [r['chg'] for r in e]
e_wins = [c4 for c4 in e_chgs if c4 > 0]
print('\n方案E：价格>=10 + 量比>=0.05 + 回踩不深:')
print(f'  触发{len(e_chgs)}次 胜率{len(e_wins)/len(e_chgs)*100:.1f}% 收益{statistics.mean(e_chgs):+.2f}%')

# ===== 方案F：价格10-50（最优价格区间）+ 量比>=0.05 =====
f = [r for r in results if 10 <= r['buy_price'] <= 50 and r['vol_ratio'] >= 0.05]
f_chgs = [r['chg'] for r in f]
f_wins = [c5 for c5 in f_chgs if c5 > 0]
print('\n方案F：价格10-50 + 量比>=0.05:')
print(f'  触发{len(f_chgs)}次 胜率{len(f_wins)/len(f_chgs)*100:.1f}% 收益{statistics.mean(f_chgs):+.2f}%')

# ===== 方案G：价格10-50 + 量比0.05~0.7 =====
g = [r for r in results if 10 <= r['buy_price'] <= 50 and 0.05 <= r['vol_ratio'] <= 0.7]
g_chgs = [r['chg'] for r in g]
g_wins = [c6 for c6 in g_chgs if c6 > 0]
print('\n方案G：价格10-50 + 量比0.05~0.7:')
print(f'  触发{len(g_chgs)}次 胜率{len(g_wins)/len(g_chgs)*100:.1f}% 收益{statistics.mean(g_chgs):+.2f}%')

# ===== 基准 =====
# 全部涨停次日开盘买入
benchmark_all = []
zt_dates = [r[0] for r in cur.execute(
    "SELECT DISTINCT trade_date FROM daily_zt WHERE trade_date >= '2026-01-01' ORDER BY trade_date"
).fetchall()]

for zt_date in zt_dates:
    next_date = cur.execute(
        "SELECT MIN(date) FROM daily_k WHERE date>?", (zt_date,)
    ).fetchone()[0]
    if not next_date:
        continue
    
    rows = cur.execute("""
        SELECT z.code, k.open FROM daily_zt z
        JOIN daily_k k ON z.code=k.code AND k.date=?
        WHERE z.trade_date=?
    """, (next_date, zt_date)).fetchall()
    
    for code, buy_price in rows:
        future = cur.execute("""
            SELECT close FROM daily_k WHERE code=? AND date>? ORDER BY date LIMIT 5
        """, (code, next_date)).fetchall()
        if len(future) >= 3:
            sell_price = future[min(4, len(future)-1)][0]
            chg = (sell_price - buy_price) / buy_price * 100
            benchmark_all.append(chg)

bm_wins = [c for c in benchmark_all if c > 0]
print('\n' + '=' * 60)
print('最终对比')
print('=' * 60)
print(f'{"策略":<35} {"触发":<8} {"胜率":<10} {"收益":<10}')
print('-' * 60)
print(f'{"全部涨停(基准)":<35} {len(benchmark_all):<8} {len(bm_wins)/len(benchmark_all)*100:<10.1f}% {statistics.mean(benchmark_all):<+10.2f}%')
print(f'{"原策略(缩量+不破底)":<35} {len(all_chgs):<8} {len(all_wins)/len(all_chgs)*100:<10.1f}% {statistics.mean(all_chgs):<+10.2f}%')
print(f'{"方案D(价格>=10+量比>=0.05)":<35} {len(d_chgs):<8} {len(d_wins)/len(d_chgs)*100:<10.1f}% {statistics.mean(d_chgs):<+10.2f}%')
print(f'{"方案E(D+回踩不深)":<35} {len(e_chgs):<8} {len(e_wins)/len(e_chgs)*100:<10.1f}% {statistics.mean(e_chgs):<+10.2f}%')
print(f'{"方案F(价格10-50+量比>=0.05)":<35} {len(f_chgs):<8} {len(f_wins)/len(f_chgs)*100:<10.1f}% {statistics.mean(f_chgs):<+10.2f}%')
print(f'{"方案G(价格10-50+量比0.05~0.7)":<35} {len(g_chgs):<8} {len(g_wins)/len(g_chgs)*100:<10.1f}% {statistics.mean(g_chgs):<+10.2f}%')

print()
best = max([(n, len(r), statistics.mean([x['chg'] for x in r])) for n, r in [('D', d), ('E', e), ('F', f), ('G', g)]], key=lambda x: x[2])
print(f'最佳方案: {best[0]} (触发{best[1]}次 收益{best[2]:+.2f}%)')

db.close()