# -*- coding: utf-8 -*-
"""Fetch comprehensive data for thesis creation"""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = r'F:\market_data.db'
conn = sqlite3.connect(DB)

holdings = [
    ('sz.002837', '英维克', 100.86, '2026-03-16'),
    ('sh.601888', '中国中免', 75.11, '2026-03-16'),
]

for code, name, buy_price, buy_date in holdings:
    rows = conn.execute(
        "SELECT date, close, volume, open, high, low FROM daily_k WHERE code=? ORDER BY date DESC LIMIT 120",
        (code,)
    ).fetchall()
    
    if not rows:
        print(f"{name}: no data")
        continue
    
    dates = [r[0] for r in rows]
    closes = [r[1] for r in rows]
    volumes = [r[2] for r in rows]
    highs = [r[3] for r in rows]  # wait, wrong order
    
    # Re-parse
    closes = [r[1] for r in rows]
    volumes = [r[2] for r in rows]
    highs = [r[4] for r in rows]
    lows = [r[5] for r in rows]
    opens = [r[3] for r in rows]
    
    latest = rows[0]
    latest_date, latest_close = latest[0], latest[1]
    
    # Moving averages
    def sma(arr, n):
        if len(arr) < n: return sum(arr)/len(arr)
        return sum(arr[-n:])/n
    
    # Recent performance
    chg_1d = (closes[0] - closes[1]) / closes[1] * 100 if len(closes) > 1 else 0
    chg_5d = (closes[0] - closes[min(5, len(closes)-1)]) / closes[min(5, len(closes)-1)] * 100
    chg_10d = (closes[0] - closes[min(10, len(closes)-1)]) / closes[min(10, len(closes)-1)] * 100
    chg_20d = (closes[0] - closes[min(20, len(closes)-1)]) / closes[min(20, len(closes)-1)] * 100
    chg_60d = (closes[0] - closes[min(60, len(closes)-1)]) / closes[min(60, len(closes)-1)] * 100
    chg_from_buy = (latest_close - buy_price) / buy_price * 100
    
    # Volume analysis
    avg_vol_5 = sum(volumes[:5]) / 5
    avg_vol_20 = sum(volumes[:20]) / 20
    vol_ratio_5 = volumes[0] / avg_vol_5 if avg_vol_5 > 0 else 1
    vol_ratio_20 = volumes[0] / avg_vol_20 if avg_vol_20 > 0 else 1
    
    # Trend analysis
    ma5 = sma(closes, 5)
    ma10 = sma(closes, 10)
    ma20 = sma(closes, 20)
    ma60 = sma(closes, 60)
    
    # Support/resistance levels (recent swings)
    high_20 = max(closes[:20])
    low_20 = min(closes[:20])
    high_60 = max(closes[:60]) if len(closes) >= 60 else max(closes)
    low_60 = min(closes[:60]) if len(closes) >= 60 else min(closes)
    
    # Price position relative to key levels
    price_to_ma5 = (latest_close - ma5) / ma5 * 100
    price_to_ma10 = (latest_close - ma10) / ma10 * 100
    price_to_ma20 = (latest_close - ma20) / ma20 * 100
    
    # Volume trend (increasing or decreasing)
    vol_trend = avg_vol_5 / avg_vol_20 if avg_vol_20 > 0 else 1
    
    # ATR-like volatility
    true_ranges = []
    for i in range(min(10, len(rows))):
        if i + 1 < len(rows):
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i+1]), abs(lows[i] - closes[i+1]))
            true_ranges.append(tr)
    atr = sum(true_ranges) / len(true_ranges) if true_ranges else 0
    
    print(f"\n{'='*60}")
    print(f"{name}({code.replace('sz.','').replace('sh.','')})")
    print(f"买入: {buy_price:.2f} @ {buy_date} | 现价: {latest_close:.2f} @ {latest_date}")
    print(f"浮盈: {chg_from_buy:+.1f}%")
    print(f"\nMA: MA5={ma5:.2f}({price_to_ma5:+.1f}%) | MA10={ma10:.2f}({price_to_ma10:+.1f}%) | MA20={ma20:.2f}({price_to_ma20:+.1f}%) | MA60={ma60:.2f}")
    print(f"涨跌: 1日{chg_1d:+.2f}% | 5日{chg_5d:+.2f}% | 10日{chg_10d:+.2f}% | 20日{chg_20d:+.2f}% | 60日{chg_60d:+.2f}%")
    print(f"量比: 5日={vol_ratio_5:.2f} | 20日={vol_ratio_20:.2f}")
    print(f"区间: 近20日高{high_20:.2f}/低{low_20:.2f} | 近60日高{high_60:.2f}/低{low_60:.2f}")
    print(f"距高点: {(latest_close-high_20)/high_20*100:+.1f}% | 距低点: {(latest_close-low_20)/low_20*100:+.1f}%")
    print(f"ATR(10日平均): {atr:.2f}")
    
    # Determine trend state
    if latest_close > ma5 > ma10 > ma20:
        trend = "强势多头"
    elif latest_close > ma20:
        trend = "偏弱震荡"
    elif latest_close < ma5 < ma10 < ma20:
        trend = "弱势空头"
    else:
        trend = "震荡无序"
    
    print(f"趋势判断: {trend}")
    
    # Volume trend
    if vol_trend > 1.2:
        vol_state = "放量"
    elif vol_trend < 0.8:
        vol_state = "缩量"
    else:
        vol_state = "正常"
    print(f"量能状态: {vol_state}")

conn.close()
