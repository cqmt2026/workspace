# -*- coding: utf-8 -*-
"""
深入分析缩量不破底策略的亏损原因，找到优化方向
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import sqlite3, json, statistics
from collections import Counter

db = sqlite3.connect('F:/market_data.db')
cur = db.cursor()

# 加载之前的回测结果
with open('out_data/zt_signal_backtest_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data['signal_results']
print(f'总交易: {len(results)}笔')

wins = [r for r in results if r['chg'] > 0]
losses = [r for r in results if r['chg'] <= 0]
big_losses = [r for r in results if r['chg'] < -10]

print(f'盈利: {len(wins)}笔 ({len(wins)/len(results)*100:.1f}%)')
print(f'亏损: {len(losses)}笔 ({len(losses)/len(results)*100:.1f}%)')
print(f'大亏(>10%): {len(big_losses)}笔 ({len(big_losses)/len(results)*100:.1f}%)')
print()

# ===== 分析1：买入价与涨停价的关系 =====
print('=' * 60)
print('分析1：涨停类型与收益的关系')
print('=' * 60)

type_stats = {}
for r in results:
    tp = r.get('type', '未知')
    if tp not in type_stats:
        type_stats[tp] = []
    type_stats[tp].append(r['chg'])

for tp, chgs in sorted(type_stats.items()):
    win = [c for c in chgs if c > 0]
    print(f'  {tp}: 触发{len(chgs)}次 胜率{len(win)/len(chgs)*100:.0f}% 收益{statistics.mean(chgs):+.2f}%')

# ===== 分析2：量比与收益的关系 =====
print()
print('=' * 60)
print('分析2：量比与收益的关系（缩量越狠越好？）')
print('=' * 60)

# 按量比分段
vol_buckets = [(0, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 0.9)]
for lo, hi in vol_buckets:
    chunk = [r for r in results if lo <= r['vol_ratio'] < hi]
    if chunk:
        win = [r for r in chunk if r['chg'] > 0]
        print(f'  量比{lo}-{hi}: 触发{len(chunk)}次 胜率{len(win)/len(chunk)*100:.0f}% 收益{statistics.mean([r["chg"] for r in chunk]):+.2f}%')

# ===== 分析3：价比（最低价比值）与收益的关系 =====
print()
print('=' * 60)
print('分析3：价比（不破底的程度）与收益的关系')
print('=' * 60)

low_buckets = [(0.99, 1.0), (1.0, 1.01), (1.01, 1.03), (1.03, 1.10)]
for lo, hi in low_buckets:
    chunk = [r for r in results if lo <= r['low_ratio'] < hi]
    if chunk:
        win = [r for r in chunk if r['chg'] > 0]
        print(f'  价比{lo}-{hi}: 触发{len(chunk)}次 胜率{len(win)/len(chunk)*100:.0f}% 收益{statistics.mean([r["chg"] for r in chunk]):+.2f}%')

# ===== 分析4：价格区间 =====
print()
print('=' * 60)
print('分析4：买入价格区间与收益')
print('=' * 60)

price_buckets = [(0, 10), (10, 20), (20, 50), (50, 100), (100, 9999)]
for lo, hi in price_buckets:
    chunk = [r for r in results if lo <= r['buy_price'] < hi]
    if chunk:
        win = [r for r in chunk if r['chg'] > 0]
        avg = statistics.mean([r['chg'] for r in chunk])
        print(f'  价格{lo}-{hi}元: 触发{len(chunk)}次 胜率{len(win)/len(chunk)*100:.0f}% 收益{avg:+.2f}%')

# ===== 分析5：大跌股的特征（找出规律） =====
print()
print('=' * 60)
print('分析5：大亏股的特征（<-10%）')
print('=' * 60)

for r in sorted(big_losses, key=lambda x: x['chg']):
    code = r['code']
    zt_date = r['zt_date']
    buy_date = r['buy_date']
    
    # 查涨停日的成交量、换手率
    zt_info = cur.execute("""
        SELECT k.volume, k.close, k.open, k.high, k.low
        FROM daily_k k WHERE k.code=? AND k.date=?
    """, (code, zt_date)).fetchone()
    
    buy_info = cur.execute("""
        SELECT k.volume, k.close, k.open, k.high, k.low
        FROM daily_k k WHERE k.code=? AND k.date=?
    """, (code, buy_date)).fetchone()
    
    zt_vol = zt_info[0] if zt_info else 0
    buy_vol = buy_info[0] if buy_info else 0
    
    # 涨停前一日的收盘价（看是不是一字板）
    prev_k = cur.execute("""
        SELECT close FROM daily_k WHERE code=? AND date<? ORDER BY date DESC LIMIT 1
    """, (code, zt_date)).fetchone()
    prev_close = prev_k[0] if prev_k else 0
    
    # 涨停涨幅
    zt_chg = (zt_info[1] - prev_close) / prev_close * 100 if prev_close > 0 else 0
    
    print(f'  {r["chg"]:+.1f}% | {zt_date} {code} | 涨停涨幅{zt_chg:.1f}% | 涨停量{zt_vol:.0f} | 次日量{buy_vol:.0f} | 买入价{r["buy_price"]:.2f} | 量比{r["vol_ratio"]}')

# ===== 分析6：有没有更好的量比阈值 =====
print()
print('=' * 60)
print('分析6：寻找最优量比阈值')
print('=' * 60)

for threshold in [0.5, 0.6, 0.7, 0.8]:
    chunk = [r for r in results if r['vol_ratio'] < threshold]
    if chunk:
        win = [r for r in chunk if r['chg'] > 0]
        avg = statistics.mean([r['chg'] for r in chunk])
        print(f'  量比<{threshold}: 触发{len(chunk)}次 胜率{len(win)/len(chunk)*100:.0f}% 收益{avg:+.2f}%')

# 同时分析 量比<0.5
print()
print('量比<0.5 的详细分析:')
tight = [r for r in results if r['vol_ratio'] < 0.5]
if tight:
    win_t = [r for r in tight if r['chg'] > 0]
    print(f'  触发{len(tight)}次 胜率{len(win_t)/len(tight)*100:.0f}% 收益{statistics.mean([r["chg"] for r in tight]):+.2f}%')

# ===== 分析7：加入市值/板块过滤的可能性 =====
print()
print('=' * 60)
print('分析7：亏损股是否集中在特定板块？')
print('=' * 60)

# 检查大亏股的前缀分布
codes_big = [r['code'] for r in big_losses]
print(f'大亏股前缀: {Counter([c.split(".")[0] for c in codes_big])}')
print(f'大亏股列表: {codes_big}')

db.close()
print()
print('分析完成')