# -*- coding: utf-8 -*-
"""Fetch recent K-line data for thesis checking"""
import sqlite3, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = r'F:\market_data.db'
PORTFOLIO = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\portfolio.json'

conn = sqlite3.connect(DB)

# Load portfolio
with open(PORTFOLIO, 'r', encoding='utf-8') as f:
    pf = json.load(f)

for h in pf.get('holdings', []):
    code = h.get('code', '')
    name = h.get('name', '')
    buy_price = h.get('entry_price', 0)
    
    # Try multiple code formats
    rows = None
    for fmt in [code, f'sz.{code}', f'sh.{code}', code]:
        r = conn.execute(
            "SELECT date, close, volume, open, high, low FROM daily_k WHERE code=? ORDER BY date DESC LIMIT 30",
            (fmt,)
        ).fetchall()
        if r:
            rows = r
            used_fmt = fmt
            break
    
    if not rows:
        print(f"{name}({code}): 无K线数据")
        continue
    
    closes = [r[1] for r in reversed(rows)]
    volumes = [r[2] for r in reversed(rows)]
    latest_date, latest_close = rows[0][0], rows[0][1]
    
    ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else closes[-1]
    ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else closes[-1]
    ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else sum(closes) / len(closes)
    
    avg_vol5 = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else volumes[-1]
    vol_ratio = volumes[-1] / avg_vol5 if avg_vol5 > 0 else 1
    
    pnl = (latest_close - buy_price) / buy_price * 100 if buy_price > 0 else 0
    
    chg_5d = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
    chg_10d = (closes[-1] - closes[-10]) / closes[-10] * 100 if len(closes) >= 10 else 0
    chg_20d = (closes[-1] - closes[-20]) / closes[-20] * 100 if len(closes) >= 20 else 0
    
    # High/lows in recent period
    high_20 = max(closes[-20:]) if len(closes) >= 20 else max(closes)
    low_20 = min(closes[-20:]) if len(closes) >= 20 else min(closes)
    dist_from_high = (latest_close - high_20) / high_20 * 100
    dist_from_low = (latest_close - low_20) / low_20 * 100
    
    print(f"\n{'='*50}")
    print(f"{name}({code}) [{used_fmt}]")
    print(f"  买入价: {buy_price:.2f} | 现价: {latest_close:.2f} | 浮盈: {pnl:+.1f}%")
    print(f"  日期: {latest_date}")
    print(f"  MA5={ma5:.2f} | MA10={ma10:.2f} | MA20={ma20:.2f}")
    print(f"  价格>MA5: {latest_close > ma5} | >MA10: {latest_close > ma10} | >MA20: {latest_close > ma20}")
    print(f"  量比(5日): {vol_ratio:.2f}")
    print(f"  5日涨跌: {chg_5d:+.2f}% | 10日: {chg_10d:+.2f}% | 20日: {chg_20d:+.2f}%")
    print(f"  近20日最高: {high_20:.2f} | 最低: {low_20:.2f}")
    print(f"  距高点: {dist_from_high:+.1f}% | 距低点: {dist_from_low:+.1f}%")

conn.close()
