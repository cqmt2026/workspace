# -*- coding: utf-8 -*-
"""
【严格完整版 v2】斌哥涨停确认信号回测
==============================
严格按照视频中的四个信号条件，全量数据验证
避免复杂索引，全部用get_next_klines逐段获取
"""
import sqlite3
from datetime import datetime, timedelta
import statistics, math, sys

db = sqlite3.connect('F:/market_data.db')
cur = db.cursor()
cur.execute("PRAGMA cache_size=-80000")

print("=" * 70)
print("斌哥涨停确认信号 — 严格完整回测 v2")
print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("数据范围: 2026年全部涨停")
print("=" * 70)

# ===== 获取涨停数据 =====
zt_list = cur.execute("""
    SELECT z.id, z.code, z.name, z.trade_date, z.close_price as zt_close,
           z.open_price as zt_open, z.zt_type
    FROM daily_zt z
    WHERE z.trade_date >= '2026-01-01'
    ORDER BY z.trade_date
""").fetchall()

# 补涨停最低价
zt_data = []
for z in zt_list:
    k = cur.execute("SELECT low, close, open, volume FROM daily_k WHERE code=? AND date=?", (z[1], z[3])).fetchone()
    if k:
        zt_data.append((z[0], z[1], z[2], z[3], z[4], z[5], k[0], z[6]))  # id,code,name,date,zt_close,zt_open,zt_low,zt_type

print(f"涨停记录: {len(zt_data)}条")

def get_k(code, date):
    """获取单日K线"""
    return cur.execute("SELECT date, open, high, low, close, volume FROM daily_k WHERE code=? AND date=?", (code, date)).fetchone()

def get_klines(code, after_date, limit=20):
    """获取某日之后的K线"""
    return cur.execute("""
        SELECT date, open, high, low, close, volume FROM daily_k 
        WHERE code=? AND date>? ORDER BY date LIMIT ?
    """, (code, after_date, limit)).fetchall()

# ===== 信号一：多阴铁底 =====
print("\n" + "=" * 70)
print("信号一：多阴铁底")
print("条件：涨停后连收3~7根阴线，最低价不破涨停最低价")
print("买入：放量阳线站上EMA20均线")
print("持有：5个交易日")
print("=" * 70)

s1_results = []

for z in zt_data:
    code, zt_date, zt_close, zt_low = z[1], z[3], z[4], z[6]
    klines = get_klines(code, zt_date, 25)
    if len(klines) < 8:
        continue
    
    # 找3~7根连续阴线，不破涨停最低价
    i = 0
    while i < len(klines):
        k = klines[i]
        if k[4] < k[1]:  # 阴线
            yin_count = 1
            yin_min_low = k[3]
            j = i + 1
            while j < len(klines) and j - i < 7:
                k2 = klines[j]
                if k2[4] < k2[1]:
                    yin_count += 1
                    yin_min_low = min(yin_min_low, k2[3])
                    j += 1
                else:
                    break
            
            if 3 <= yin_count <= 7 and yin_min_low >= zt_low * 0.995:
                # 找后续放量阳线站上EMA20
                # 取前20个close算EMA
                for m in range(j, min(j + 10, len(klines))):
                    buy_k = klines[m]
                    if buy_k[4] <= buy_k[1]:  # 不是阳线
                        continue
                    
                    # 计算EMA20
                    hist = cur.execute("""
                        SELECT close FROM daily_k WHERE code=? AND date<=? AND date>=?
                        ORDER BY date DESC LIMIT 20
                    """, (code, buy_k[0], zt_date)).fetchall()
                    hist = list(reversed(hist))
                    hist_closes = [h[0] for h in hist] + [buy_k[4]]
                    
                    if len(hist_closes) < 20:
                        continue
                    
                    alpha = 2/21
                    ema = hist_closes[0]
                    for c in hist_closes[1:]:
                        ema = c * alpha + ema * (1-alpha)
                    
                    if buy_k[4] < ema:  # 没站上EMA20
                        continue
                    
                    # 放量（>前20日均量*1.2）
                    hist_vol = cur.execute("""
                        SELECT volume FROM daily_k WHERE code=? AND date<=? AND date>?
                        ORDER BY date DESC LIMIT 20
                    """, (code, buy_k[0], zt_date)).fetchall()
                    vol_list = [v[0] for v in hist_vol]
                    vol_ma = sum(vol_list) / len(vol_list) if vol_list else 0
                    
                    if buy_k[5] <= vol_ma * 1.2:
                        continue
                    
                    # 买入！持有5日
                    future = get_klines(code, buy_k[0], 6)
                    if len(future) >= 5:
                        buy_p = buy_k[4]
                        sell_p = future[4][4]
                        chg = (sell_p - buy_p) / buy_p * 100
                        s1_results.append(chg)
                    break
            i = j
        else:
            i += 1

print(f"触发次数: {len(s1_results)}")
if s1_results:
    wins = [r for r in s1_results if r > 0]
    losses = [r for r in s1_results if r <= 0]
    print(f"胜率: {len(wins)/len(s1_results)*100:.1f}%")
    print(f"平均收益: {statistics.mean(s1_results):.2f}%")
    print(f"中位数: {statistics.median(s1_results):.2f}%")
    print(f"最大收益: {max(s1_results):.2f}%")
    print(f"最大亏损: {min(s1_results):.2f}%")
    if wins and losses:
        print(f"盈亏比: {abs(statistics.mean(wins))/abs(statistics.mean(losses)):.2f}")

# ===== 信号二：半量阴号 =====
print("\n" + "=" * 70)
print("信号二：半量阴号")
print("条件：涨停后5日内出现阴线，量较前一日萎缩一半以上(<50%)")
print("买入：后续阳线收盘突破该阴线开盘价")
print("持有：5个交易日")
print("=" * 70)

s2_results = []

for z in zt_data:
    code, zt_date = z[1], z[3]
    zt_k = get_k(code, zt_date)
    if not zt_k or zt_k[5] <= 0:
        continue
    zt_vol = zt_k[5]
    
    klines = get_klines(code, zt_date, 10)
    if len(klines) < 2:
        continue
    
    found = False
    for i in range(min(5, len(klines))):
        if found:
            break
        k = klines[i]
        if k[4] >= k[1]:  # 不是阴线
            continue
        
        # 前一日成交量
        if i == 0:
            prev_vol = zt_vol
        else:
            prev_vol = klines[i-1][5]
        
        if k[5] >= prev_vol * 0.5:  # 量没缩一半
            continue
        
        # 找后续阳线突破阴线开盘价
        for j in range(i+1, min(i+5, len(klines))):
            k2 = klines[j]
            if k2[4] > k[1]:  # 阳线收盘突破阴线开盘价
                future = get_klines(code, k2[0], 6)
                if len(future) >= 5:
                    buy_p = k2[4]
                    sell_p = future[4][4]
                    chg = (sell_p - buy_p) / buy_p * 100
                    s2_results.append(chg)
                    found = True
                break

print(f"触发次数: {len(s2_results)}")
if s2_results:
    wins = [r for r in s2_results if r > 0]
    losses = [r for r in s2_results if r <= 0]
    print(f"胜率: {len(wins)/len(s2_results)*100:.1f}%")
    print(f"平均收益: {statistics.mean(s2_results):.2f}%")
    print(f"中位数: {statistics.median(s2_results):.2f}%")
    print(f"最大收益: {max(s2_results):.2f}%")
    print(f"最大亏损: {min(s2_results):.2f}%")
    if wins and losses:
        print(f"盈亏比: {abs(statistics.mean(wins))/abs(statistics.mean(losses)):.2f}")

# ===== 信号三：四星起势 =====
print("\n" + "=" * 70)
print("信号三：四星起势")
print("条件：涨停后股价在涨停实体上方横盘4~5根小阳/十字星，量递减")
print("买入：放量阳线突破")
print("持有：5个交易日")
print("=" * 70)

s3_results = []

for z in zt_data:
    code, zt_date, zt_close = z[1], z[3], z[4]
    klines = get_klines(code, zt_date, 20)
    if len(klines) < 6:
        continue
    
    for i in range(len(klines) - 5):
        cluster = klines[i:i+5]
        
        # 都在涨停实体上方（最低价>=涨停价*0.97）
        if any(k[3] < zt_close * 0.97 for k in cluster):
            continue
        
        # 都是小阳/十字星（实体<3%，振幅<4%）
        if any(abs(k[4]-k[1])/k[1]*100 >= 3 or (k[2]-k[3])/k[3]*100 >= 4 for k in cluster):
            continue
        
        # 量递减
        vols = [k[5] for k in cluster]
        if any(vols[j] > vols[j-1] * 1.1 for j in range(1, len(vols))):
            continue
        
        # 后续放量阳线突破
        if i+5 >= len(klines):
            continue
        bk = klines[i+5]
        
        if bk[4] <= bk[1]:  # 不是阳线
            continue
        
        # 放量
        vol_ma = sum(vols) / 5
        if bk[5] <= vol_ma * 1.3:
            continue
        
        # 突破前5日最高
        if bk[4] <= max(k[2] for k in cluster):
            continue
        
        # 买入
        future = get_klines(code, bk[0], 6)
        if len(future) >= 5:
            buy_p = bk[4]
            sell_p = future[4][4]
            chg = (sell_p - buy_p) / buy_p * 100
            s3_results.append(chg)

print(f"触发次数: {len(s3_results)}")
if s3_results:
    wins = [r for r in s3_results if r > 0]
    losses = [r for r in s3_results if r <= 0]
    print(f"胜率: {len(wins)/len(s3_results)*100:.1f}%")
    print(f"平均收益: {statistics.mean(s3_results):.2f}%")
    print(f"中位数: {statistics.median(s3_results):.2f}%")
    print(f"最大收益: {max(s3_results):.2f}%")
    print(f"最大亏损: {min(s3_results):.2f}%")
    if wins and losses:
        print(f"盈亏比: {abs(statistics.mean(wins))/abs(statistics.mean(losses)):.2f}")

# ===== 信号四：仙人指路 =====
print("\n" + "=" * 70)
print("信号四：仙人指路搓洗盘")
print("条件：涨停后第1天长上影+第2天阴线+第3天阳包阴")
print("买入：第3天阳包阴收盘买入")
print("持有：5个交易日")
print("=" * 70)

s4_results = []

for z in zt_data:
    code, zt_date = z[1], z[3]
    klines = get_klines(code, zt_date, 10)
    if len(klines) < 5:
        continue
    
    for i in range(len(klines) - 3):
        k1, k2, k3 = klines[i], klines[i+1], klines[i+2]
        
        # 第1天：长上影
        body1 = abs(k1[4] - k1[1])
        upper1 = k1[2] - max(k1[1], k1[4])
        if upper1 < body1 * 2 or upper1 < k1[4] * 0.02:
            continue
        
        # 第2天：低开低走阴线
        if k2[1] >= k1[4]:  # 没低开
            continue
        if k2[4] >= k2[1]:  # 不是阴线
            continue
        
        # 第3天：阳包阴
        if k3[4] <= k3[1]:  # 不是阳线
            continue
        if k3[4] <= k2[1] or k3[1] >= k2[4]:  # 没包住
            continue
        
        # 买入
        future = get_klines(code, k3[0], 6)
        if len(future) >= 5:
            buy_p = k3[4]
            sell_p = future[4][4]
            chg = (sell_p - buy_p) / buy_p * 100
            s4_results.append(chg)

print(f"触发次数: {len(s4_results)}")
if s4_results:
    wins = [r for r in s4_results if r > 0]
    losses = [r for r in s4_results if r <= 0]
    print(f"胜率: {len(wins)/len(s4_results)*100:.1f}%")
    print(f"平均收益: {statistics.mean(s4_results):.2f}%")
    print(f"中位数: {statistics.median(s4_results):.2f}%")
    print(f"最大收益: {max(s4_results):.2f}%")
    print(f"最大亏损: {min(s4_results):.2f}%")
    if wins and losses:
        print(f"盈亏比: {abs(statistics.mean(wins))/abs(statistics.mean(losses)):.2f}")

# ===== 基准：无脑打板 =====
print("\n" + "=" * 70)
print("基准：无脑打板（涨停次日开盘买入，持有5日）")
print("=" * 70)

bm_results = []
for z in zt_data:
    code, zt_date = z[1], z[3]
    klines = get_klines(code, zt_date, 7)
    if len(klines) >= 6:
        buy_p = klines[0][1]  # 次日开盘
        sell_p = klines[4][4]  # 第5日收盘
        chg = (sell_p - buy_p) / buy_p * 100
        bm_results.append(chg)

print(f"触发次数: {len(bm_results)}")
if bm_results:
    wins = [r for r in bm_results if r > 0]
    losses = [r for r in bm_results if r <= 0]
    print(f"胜率: {len(wins)/len(bm_results)*100:.1f}%")
    print(f"平均收益: {statistics.mean(bm_results):.2f}%")
    print(f"中位数: {statistics.median(bm_results):.2f}%")
    print(f"最大收益: {max(bm_results):.2f}%")
    print(f"最大亏损: {min(bm_results):.2f}%")
    if wins and losses:
        print(f"盈亏比: {abs(statistics.mean(wins))/abs(statistics.mean(losses)):.2f}")

# ===== 汇总 =====
print("\n" + "=" * 70)
print("最终汇总对比")
print("=" * 70)
print(f"{'策略':<20} {'触发':<8} {'胜率':<10} {'平均收益':<12} {'中位数':<10} {'最大收益':<10} {'最大亏损':<10} {'盈亏比':<10}")
print("-" * 70)

strategies = [
    ("无脑打板(基准)", bm_results),
    ("多阴铁底(信号一)", s1_results),
    ("半量阴号(信号二)", s2_results),
    ("四星起势(信号三)", s3_results),
    ("仙人指路(信号四)", s4_results),
]

for name, res in strategies:
    if res:
        wins = [r for r in res if r > 0]
        losses = [r for r in res if r <= 0]
        wr = len(wins)/len(res)*100
        avg = statistics.mean(res)
        med = statistics.median(res)
        mx = max(res)
        mn = min(res)
        rr = abs(statistics.mean(wins))/abs(statistics.mean(losses)) if wins and losses else 0
        print(f"{name:<20} {len(res):<8} {wr:<10.1f}% {avg:<12.2f}% {med:<10.2f}% {mx:<10.2f}% {mn:<10.2f}% {rr:<10.2f}")
    else:
        print(f"{name:<20} 0      N/A        N/A          N/A        N/A        N/A        N/A")

print("\n" + "=" * 70)
print("结论")
print("=" * 70)

# 简单结论
if bm_results:
    bm_avg = statistics.mean(bm_results)
    bm_win = len([r for r in bm_results if r > 0]) / len(bm_results) * 100

best_name, best_avg = "", -999
for name, res in strategies:
    if res and statistics.mean(res) > best_avg:
        best_avg = statistics.mean(res)
        best_name = name

print(f"""
基准(无脑打板): 胜率{bm_win:.1f}% 收益{bm_avg:.2f}%
最佳信号: {best_name} 收益{best_avg:.2f}%

关键发现:
1. {'斌哥策略优于无脑打板' if best_avg > bm_avg else '斌哥策略整体不如无脑打板'}
2. 信号触发次数普遍偏少，属于低频策略
3. {'四星起势(信号三)表现最好' if '四星起势' in best_name else '多阴铁底(信号一)表现最好' if '多阴铁底' in best_name else '半量阴号(信号二)表现最好' if '半量阴号' in best_name else '仙人指路(信号四)表现最好' if '仙人指路' in best_name else ''}
4. 建议结合大盘环境筛选（非单边下跌市）
""")

db.close()
print("回测完成")