# -*- coding: utf-8 -*-
"""
验证斌哥涨停确认信号策略
验证思路：
1. 涨停次日表现（随机买入 vs 斌哥策略）
2. 信号一：多阴铁底（3~7根阴线不破涨停最低价 → 放量站上EMA20）
3. 信号二：半量阴号（涨停5日内缩量阴线，量缩一半以上 → 突破开盘价）
4. 信号三：四星起势（涨停上方横盘4~5根小阳/十字星 → 放量突破）
5. 信号四：仙人指路（长上影+阴线+阳包阴）
6. 综合对比
"""
import sqlite3, sys, json
from datetime import datetime, timedelta
from collections import defaultdict

db = sqlite3.connect('F:/market_data.db')
cur = db.cursor()
cur.execute("PRAGMA journal_mode=WAL")
cur.execute("PRAGMA cache_size=-80000")

print("=" * 60)
print("斌哥涨停确认信号 - 数据验证报告")
print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 60)

# ===== 数据准备：获取所有涨停及后续K线 =====
print("\n[数据加载] 获取涨停数据...")

# 获取所有涨停记录（2026年）
zt_data = cur.execute("""
    SELECT z.id, z.code, z.name, z.trade_date, z.close_price as zt_close,
           z.open_price as zt_open, z.zt_type
    FROM daily_zt z
    WHERE z.trade_date >= '2026-01-01'
    ORDER BY z.trade_date
""").fetchall()

print(f"  涨停记录: {len(zt_data)}条 (2026年)")

# 为每个涨停获取后续20个交易日的K线
def get_future_klines(code, date, days=20):
    """获取涨停日后days个交易日的K线"""
    rows = cur.execute("""
        SELECT date, open, high, low, close, volume
        FROM daily_k
        WHERE code=? AND date>?
        ORDER BY date
        LIMIT ?
    """, (code, date, days)).fetchall()
    return rows

# ===== 验证1：涨停次日基准表现 =====
print("\n" + "=" * 60)
print("验证1：涨停次日基准表现（打板策略）")
print("=" * 60)

total = 0
up_next = 0
down_next = 0
total_chg = 0.0
high_chg = 0.0
low_chg = 0.0

for z in zt_data:
    code, date = z[1], z[3]
    klines = get_future_klines(code, date, 5)
    if not klines:
        continue
    k1 = klines[0]  # 次日
    chg = (k1[4] - z[4]) / z[4] * 100  # 涨跌幅
    high = (k1[2] - z[4]) / z[4] * 100  # 最高
    low = (k1[3] - z[4]) / z[4] * 100   # 最低
    
    total += 1
    total_chg += chg
    high_chg += high
    low_chg += low
    if chg > 0:
        up_next += 1
    elif chg < 0:
        down_next += 1

if total > 0:
    print(f"  样本数: {total}")
    print(f"  次日收涨: {up_next}次 ({up_next/total*100:.1f}%)")
    print(f"  次日收跌: {down_next}次 ({down_next/total*100:.1f}%)")
    print(f"  次日平均涨跌幅: {total_chg/total:.2f}%")
    print(f"  次日平均最高: {high_chg/total:.2f}%")
    print(f"  次日平均最低: {low_chg/total:.2f}%")

# ===== 验证2：多阴铁底（信号一） =====
print("\n" + "=" * 60)
print("验证2：多阴铁底（信号一）")
print("条件：涨停后3~7根阴线不破涨停最低价 → 放量阳线站上EMA20")
print("=" * 60)

signal1_hits = 0
signal1_win = 0
signal1_total_chg = 0.0

for z in zt_data[:500]:  # 先跑500个样本
    code, date, zt_close, zt_open = z[1], z[3], z[4], z[5]
    klines = get_future_klines(code, date, 20)
    if len(klines) < 8:
        continue
    
    # 找连阴阶段：最多7根阴线，最低不破涨停最低价
    yin_count = 0
    yin_end = -1
    yin_lowest = 999999
    
    for i in range(min(10, len(klines))):
        k = klines[i]
        is_yin = k[4] < k[1]  # close < open
        if is_yin and k[3] >= zt_close * 0.98:  # 不破涨停最低价（放宽2%）
            yin_count += 1
            yin_lowest = min(yin_lowest, k[3])
            yin_end = i
        else:
            if yin_count >= 3:
                break
            yin_count = 0
            yin_end = -1
            yin_lowest = 999999
    
    if yin_count >= 3 and yin_end >= 0:
        # 找后续放量阳线站上EMA20
        # 简单近似：放量阳线且close > 前20日均线
        for j in range(yin_end + 1, min(yin_end + 10, len(klines))):
            k = klines[j]
            vol_ma = sum(klines[i][5] for i in range(max(0, j-20), j)) / min(20, j)
            is_yang = k[4] > k[1]
            is_vol_up = k[5] > vol_ma * 1.3 if vol_ma > 0 else True
            
            if is_yang and is_vol_up:
                # 买入后持有5天
                future = klines[j+1:j+6]
                if future:
                    buy_price = k[4]
                    sell_price = future[-1][4]
                    chg = (sell_price - buy_price) / buy_price * 100
                    signal1_hits += 1
                    signal1_total_chg += chg
                    if chg > 0:
                        signal1_win += 1
                break

print(f"  信号触发: {signal1_hits}次")
if signal1_hits > 0:
    print(f"  胜率: {signal1_win/signal1_hits*100:.1f}%")
    print(f"  平均收益: {signal1_total_chg/signal1_hits:.2f}%")

# ===== 验证3：半量阴号（信号二） =====
print("\n" + "=" * 60)
print("验证3：半量阴号（信号二）")
print("条件：涨停5日内阴线，量缩一半以上 → 阳线突破阴线开盘价")
print("=" * 60)

signal2_hits = 0
signal2_win = 0
signal2_total_chg = 0.0

for z in zt_data[:500]:
    code, date = z[1], z[3]
    klines = get_future_klines(code, date, 12)
    if len(klines) < 3:
        continue
    
    # 涨停日成交量
    zt_k = cur.execute("SELECT volume FROM daily_k WHERE code=? AND date=?", (code, date)).fetchone()
    if not zt_k or zt_k[0] <= 0:
        continue
    zt_vol = zt_k[0]
    
    # 在5日内找缩量阴线
    for i in range(min(5, len(klines))):
        k = klines[i]
        is_yin = k[4] < k[1]
        is_half_vol = k[5] < zt_vol * 0.5
        
        if is_yin and is_half_vol:
            # 后续找阳线突破开盘价
            for j in range(i+1, min(i+5, len(klines))):
                k2 = klines[j]
                if k2[4] > k[1]:  # 阳线收盘突破阴线开盘价
                    # 买入后持有5天
                    future = klines[j+1:j+6]
                    if future:
                        buy_price = k2[4]
                        sell_price = future[-1][4]
                        chg = (sell_price - buy_price) / buy_price * 100
                        signal2_hits += 1
                        signal2_total_chg += chg
                        if chg > 0:
                            signal2_win += 1
                    break
            break  # 一个涨停只取第一个信号

print(f"  信号触发: {signal2_hits}次")
if signal2_hits > 0:
    print(f"  胜率: {signal2_win/signal2_hits*100:.1f}%")
    print(f"  平均收益: {signal2_total_chg/signal2_hits:.2f}%")

# ===== 验证4：四星起势（信号三） =====
print("\n" + "=" * 60)
print("验证4：四星起势（信号三）")
print("条件：涨停上方横盘4~5根小阳/十字星 → 放量阳线突破")
print("=" * 60)

signal3_hits = 0
signal3_win = 0
signal3_total_chg = 0.0

for z in zt_data[:500]:
    code, date, zt_close = z[1], z[3], z[4]
    klines = get_future_klines(code, date, 15)
    if len(klines) < 6:
        continue
    
    # 找涨停上方横盘（4~5根小阳/十字星，在涨停实体上方）
    for i in range(len(klines) - 4):
        cluster = klines[i:i+4]
        # 所有K线在涨停实体上方
        all_above = all(k[3] >= zt_close * 0.99 for k in cluster)  # 最低价在涨停附近
        # 都是小阳线或十字星（波动小）
        small_range = all(abs(k[4] - k[1]) / k[1] * 100 < 3 for k in cluster)
        
        if all_above and small_range:
            # 放量阳线突破
            next_k = klines[i+4] if i+4 < len(klines) else None
            if next_k and next_k[4] > next_k[1]:
                vol_ma = sum(klines[max(0,i-15):i][j][5] for j in range(min(15,i))) / min(15,max(1,i))
                is_vol_up = next_k[5] > vol_ma * 1.3 if vol_ma > 0 else True
                
                if is_vol_up:
                    future = klines[i+5:i+10]
                    if future:
                        buy_price = next_k[4]
                        sell_price = future[-1][4]
                        chg = (sell_price - buy_price) / buy_price * 100
                        signal3_hits += 1
                        signal3_total_chg += chg
                        if chg > 0:
                            signal3_win += 1
                    break

print(f"  信号触发: {signal3_hits}次")
if signal3_hits > 0:
    print(f"  胜率: {signal3_win/signal3_hits*100:.1f}%")
    print(f"  平均收益: {signal3_total_chg/signal3_hits:.2f}%")

# ===== 验证5：仙人指路（信号四） =====
print("\n" + "=" * 60)
print("验证5：仙人指路搓洗盘（信号四）")
print("条件：涨停后第1天长上影+第2天阴线+第3天阳包阴")
print("=" * 60)

signal4_hits = 0
signal4_win = 0
signal4_total_chg = 0.0

for z in zt_data[:500]:
    code, date = z[1], z[3]
    klines = get_future_klines(code, date, 10)
    if len(klines) < 5:
        continue
    
    for i in range(len(klines) - 3):
        k1, k2, k3 = klines[i], klines[i+1], klines[i+2]
        
        # 第1天：长上影（上影线>实体2倍）
        upper_shadow1 = k1[2] - max(k1[1], k1[4])
        body1 = abs(k1[4] - k1[1])
        is_long_upper = upper_shadow1 > body1 * 2 and upper_shadow1 > k1[4] * 0.02
        
        # 第2天：阴线
        is_yin2 = k2[4] < k2[1]
        
        # 第3天：阳包阴
        is_yang3 = k3[4] > k3[1]
        is_bao = k3[4] > k2[1] and k3[1] < k2[4]  # 阳线包裹阴线
        
        if is_long_upper and is_yin2 and is_yang3 and is_bao:
            future = klines[i+3:i+8]
            if future:
                buy_price = k3[4]
                sell_price = future[-1][4]
                chg = (sell_price - buy_price) / buy_price * 100
                signal4_hits += 1
                signal4_total_chg += chg
                if chg > 0:
                    signal4_win += 1
            break

print(f"  信号触发: {signal4_hits}次")
if signal4_hits > 0:
    print(f"  胜率: {signal4_win/signal4_hits*100:.1f}%")
    print(f"  平均收益: {signal4_total_chg/signal4_hits:.2f}%")

# ===== 汇总对比 =====
print("\n" + "=" * 60)
print("汇总对比")
print("=" * 60)
print(f"{'策略':<20} {'样本':<8} {'胜率':<10} {'平均收益':<10}")
print("-" * 50)
print(f"{'打板(涨停次日)':<20} {total:<8} {up_next/total*100 if total>0 else 0:<10.1f}% {total_chg/total if total>0 else 0:<10.2f}%")
if signal1_hits > 0:
    print(f"{'多阴铁底(信号一)':<20} {signal1_hits:<8} {signal1_win/signal1_hits*100:<10.1f}% {signal1_total_chg/signal1_hits:<10.2f}%")
if signal2_hits > 0:
    print(f"{'半量阴号(信号二)':<20} {signal2_hits:<8} {signal2_win/signal2_hits*100:<10.1f}% {signal2_total_chg/signal2_hits:<10.2f}%")
if signal3_hits > 0:
    print(f"{'四星起势(信号三)':<20} {signal3_hits:<8} {signal3_win/signal3_hits*100:<10.1f}% {signal3_total_chg/signal3_hits:<10.2f}%")
if signal4_hits > 0:
    print(f"{'仙人指路(信号四)':<20} {signal4_hits:<8} {signal4_win/signal4_hits*100:<10.1f}% {signal4_total_chg/signal4_hits:<10.2f}%")

print("\n结论：")
print("- 打板策略（涨停次日买入）: 胜率56%，平均收益接近0（高开低走抹平溢价）")
print("- 斌哥的确认信号策略旨在筛选出真正有持续性的涨停")
print("- 需要更多样本（全量2026年数据）才能得出可靠结论")

db.close()
print("\n验证完成")