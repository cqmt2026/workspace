# -*- coding: utf-8 -*-
"""
Step 2 替代方案：量价资金强度
================================
当API资金流不可用时，用DB中的量价数据推断资金行为。

逻辑：
  放量上涨 = 主动买入（资金流入）
  缩量上涨 = 跟风上涨（资金可能没进）
  放量下跌 = 资金出逃
  
指标：
  1. 量价比 = (今日涨幅%) / (今日量比) — 同等量能推动更多涨幅=买盘积极
  2. 价量趋势 = 近5日收盘价趋势与成交量趋势的一致性
  3. 相对强度 = 个股涨幅 - 板块涨幅（跑赢板块=强势）
"""
import sqlite3, json, os, sys
from datetime import date, timedelta
sys.stdout.reconfigure(encoding='utf-8')

DB = r"F:\market_data.db"

def get_volume_price_data(code, today=None):
    """获取量价数据"""
    clean_code = code[-6:] if len(code) > 6 else code
    if today is None:
        today = date.today().isoformat()
    
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # 精确查询（不走LIKE，走索引）
    # 尝试不同前缀
    prefixes = ['sh.', 'sz.', 'bj.']
    rows = []
    for prefix in prefixes:
        c.execute("""
            SELECT date, close, volume FROM daily_k 
            WHERE code = ? AND date <= ?
            ORDER BY date DESC LIMIT 25
        """, (f'{prefix}{clean_code}', today))
        rows = c.fetchall()
        if len(rows) >= 15:
            break
    
    conn.close()
    
    if len(rows) < 15:
        return None
    
    closes = [float(r[1]) for r in rows]
    volumes = [float(r[2]) for r in rows]
    
    # 均线
    ma5 = sum(closes[:5]) / 5
    ma10 = sum(closes[:10]) / 10 if len(closes) >= 10 else ma5
    ma20 = sum(closes[:min(20, len(closes))]) / min(20, len(closes))
    
    # 5日均量
    avg_vol_5 = sum(volumes[:5]) / 5
    vol_ratio = volumes[0] / avg_vol_5 if avg_vol_5 > 0 else 1
    
    # 涨幅
    chg_pct = (closes[0] - closes[1]) / closes[1] * 100 if closes[1] > 0 else 0
    chg_3d = (closes[0] - closes[3]) / closes[3] * 100 if len(closes) > 3 and closes[3] > 0 else 0
    chg_5d = (closes[0] - closes[5]) / closes[5] * 100 if len(closes) > 5 and closes[5] > 0 else 0
    
    # 量价协调性
    # 近5日价格趋势方向（线性回归斜率简化版）
    price_trend = (closes[0] - closes[4]) / 5  # 5日价格变化/5
    vol_trend = (volumes[0] - sum(volumes[1:5])/4) / (sum(volumes[1:5])/4) * 100 if sum(volumes[1:5]) > 0 else 0
    
    # 量价比 = 涨幅/量比 (同等量能推涨更多=好)
    price_efficiency = abs(chg_pct) / vol_ratio if vol_ratio > 0 and abs(chg_pct) > 0 else 0
    
    return {
        'ma5': ma5, 'ma10': ma10, 'ma20': ma20,
        'vol_ratio': vol_ratio,
        'chg_pct': chg_pct,
        'chg_3d': chg_3d,
        'chg_5d': chg_5d,
        'price_trend': price_trend,
        'vol_trend': vol_trend,
        'price_efficiency': price_efficiency,
        'close': closes[0],
    }

def get_sector_avg_chg(sector_name, today=None):
    """获取板块平均涨幅"""
    import json
    cache_file = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\stock_board_cache.json'
    
    if not os.path.exists(cache_file):
        return 0
    
    with open(cache_file, encoding='utf-8') as f:
        cache = json.load(f)
    
    if today is None:
        today = date.today().isoformat()
    
    # 找出板块内股票
    sector_stocks = []
    for code, info in cache.items():
        if isinstance(info, str) and info == sector_name:
            sector_stocks.append(code)
        elif isinstance(info, dict) and (info.get('board') == sector_name or info.get('industry') == sector_name):
            sector_stocks.append(code)
    
    if not sector_stocks:
        return 0
    
    # 取前20只计算平均涨幅
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    total_chg = 0
    count = 0
    for code in sector_stocks[:20]:
        c.execute("""
            SELECT close FROM daily_k WHERE code LIKE ? AND date = ? LIMIT 1
        """, (f'%{code}', today))
        cur = c.fetchone()
        c.execute("""
            SELECT close FROM daily_k WHERE code LIKE ? AND date < ? ORDER BY date DESC LIMIT 1
        """, (f'%{code}', today))
        prev = c.fetchone()
        if cur and prev and prev[0] > 0:
            chg = (cur[0] - prev[0]) / prev[0] * 100
            total_chg += chg
            count += 1
    conn.close()
    
    return total_chg / count if count > 0 else 0

def verify_candidates(candidates, verbose=True):
    """用量价关系验证资金流入"""
    if verbose:
        print("=" * 60)
        print("Step 2: 量价资金强度验证")
        print("=" * 60)
    
    passed = []
    failed = []
    
    for i, c in enumerate(candidates):
        code = c['code']
        name = c.get('name', code)
        
        if verbose:
            print(f"\r  [{i+1}/{len(candidates)}] {name}({code})...", end='')
        
        vp = get_volume_price_data(code)
        if vp is None:
            failed.append({**c, 'reason': 'K线数据不足'})
            continue
        
        c['vp_data'] = vp
        
        # 条件判断（简化版）
        # 1. 多头排列（MA5>MA10>MA20）
        ma_bullish = vp['ma5'] > vp['ma10'] > vp['ma20']
        
        # 2. 放量（量比>2.0 — 平衡信号数量和胜率）
        vol_up = vp['vol_ratio'] > 2.0
        
        # 3. 今日上涨
        price_up = vp['chg_pct'] > 0
        
        if ma_bullish and vol_up and price_up:
            passed.append(c)
        else:
            reasons = []
            if not ma_bullish: reasons.append('非多头')
            if not vol_up: reasons.append(f'缩量({vp["vol_ratio"]:.2f})')
            if not price_up: reasons.append(f'下跌({vp["chg_pct"]:+.1f}%)')
            failed.append({**c, 'reason': '+'.join(reasons)})
    
    if verbose:
        print()
        print(f"\n[Step2] 量价验证通过: {len(passed)}/{len(candidates)}")
        if passed:
            print(f"  通过:")
            for c in passed[:5]:
                v = c['vp_data']
                print(f"  🟢 {c.get('name','?'):10s}({c['code']}) MA多头 涨幅{v['chg_pct']:+.1f}% 量比{v['vol_ratio']:.2f}")
        if failed:
            print(f"  未通过:")
            for c in failed[:5]:
                print(f"  🔴 {c.get('name','?'):10s}({c['code']}) {c.get('reason','')}")
    
    return passed, failed

if __name__ == '__main__':
    from step1_sector_filter import run as step1_run
    step1_result = step1_run(verbose=False)
    candidates = step1_result['candidates'][:10]
    print(f"[Step2] 从Step1取前{len(candidates)}只验证量价")
    passed, failed = verify_candidates(candidates)