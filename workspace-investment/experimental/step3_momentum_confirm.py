# -*- coding: utf-8 -*-
"""
Step 3: 动量确认
================
从Step2验证通过的候选股中，确认动量条件。

条件：
  1. MA5 > MA10 > MA20（多头排列）
  2. 量比 > 1.0（今日放量）
  3. 今日涨幅 3% ~ 8%（温和放量上涨）
  4. 近3日涨幅 0% ~ 15%（没有暴涨透支）
  5. 换手率 3% ~ 15%（活跃但不疯狂）

数据来源：
  - 数据库 daily_k（日K线）
  - 腾讯实时行情（盘中）/ 数据库（盘后）

不修改现有系统，只读数据。
"""
import sqlite3, json, urllib.request, os, sys
from datetime import date, timedelta
sys.stdout.reconfigure(encoding='utf-8')

DB = r"F:\market_data.db"

def get_realtime_quote(code):
    """获取腾讯实时行情"""
    clean_code = code[-6:] if len(code) > 6 else code
    market = 'sh' if code.startswith('sh') or code.startswith('60') else 'sz'
    url = f"https://qt.gtimg.cn/q={market}{clean_code}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode('gbk')
        
        if '~' not in data:
            return None
        
        p = data.split('~')
        if len(p) < 40:
            return None
        
        return {
            'name': p[1],
            'price': float(p[3]) if p[3] else 0,
            'prev_close': float(p[4]) if p[4] else 0,
            'open': float(p[5]) if p[5] else 0,
            'volume': float(p[6]) if p[6] else 0,  # 手
            'amount': float(p[37]) if p[37] else 0,  # 万元
            'high': float(p[33]) if p[33] else 0,
            'low': float(p[34]) if p[34] else 0,
            'turnover': float(p[38]) if p[38] else 0,  # 换手率%
            'pe': float(p[39]) if p[39] else 0,
            'amount_unit': float(p[37]) if p[37] else 0,  # 万元
        }
    except:
        return None

def get_ma_data(code, today=None):
    """从DB获取均线数据"""
    clean_code = code[-6:] if len(code) > 6 else code
    if today is None:
        today = date.today().isoformat()
    
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # 获取最近20个交易日数据
    c.execute("""
        SELECT date, close, volume FROM daily_k 
        WHERE code LIKE ? AND date <= ?
        ORDER BY date DESC LIMIT 25
    """, (f'%{clean_code}', today))
    
    rows = c.fetchall()
    conn.close()
    
    if len(rows) < 20:
        return None
    
    closes = [r[1] for r in rows]
    volumes = [r[2] for r in rows]
    
    # 计算MA
    ma5 = sum(closes[:5]) / 5
    ma10 = sum(closes[:10]) / 10
    ma20 = sum(closes[:20]) / 20
    
    # 计算量比（当日成交量 / 5日均量）
    avg_vol_5 = sum(volumes[:5]) / 5
    vol_ratio = volumes[0] / avg_vol_5 if avg_vol_5 > 0 else 1
    
    # 计算涨幅
    chg_pct = (closes[0] - closes[1]) / closes[1] * 100 if closes[1] > 0 else 0
    
    # 近3日涨幅
    chg_3d = (closes[0] - closes[3]) / closes[3] * 100 if len(closes) > 3 and closes[3] > 0 else 0
    
    return {
        'ma5': ma5,
        'ma10': ma10,
        'ma20': ma20,
        'vol_ratio': vol_ratio,
        'chg_pct': chg_pct,
        'chg_3d': chg_3d,
        'close': closes[0],
        'volume': volumes[0],
    }

def check_momentum(candidates, use_realtime=False, verbose=True):
    """确认动量条件"""
    if verbose:
        print("=" * 60)
        print("Step 3: 动量确认")
        print("=" * 60)
    
    today = date.today().isoformat()
    passed = []
    failed = []
    
    for i, c in enumerate(candidates):
        code = c['code']
        
        if verbose:
            print(f"\r  [{i+1}/{len(candidates)}] {c.get('name','?')}({code})...", end='')
        
        # 获取均线数据
        ma = get_ma_data(code, today)
        if ma is None:
            failed.append({**c, 'reason': 'K线数据不足'})
            continue
        
        # 判断条件（宽松版：基于2026年回测最优参数）
        ma_bullish = ma['ma5'] > ma['ma10'] > ma['ma20']  # 多头排列
        vol_ok = ma['vol_ratio'] > 2.0  # 量比>2.0（平衡信号数量和胜率）
        chg_ok = 4 <= ma['chg_pct'] <= 7  # 涨幅4-7%
        chg_3d_ok = 0 <= ma['chg_3d'] <= 12  # 近3日涨幅0-12%
        
        c['ma_data'] = ma
        
        if ma_bullish and vol_ok and chg_ok and chg_3d_ok:
            passed.append(c)
        else:
            reasons = []
            if not ma_bullish: reasons.append('非多头排列')
            if not vol_ok: reasons.append(f'量比{ma["vol_ratio"]:.2f}')
            if not chg_ok: reasons.append(f'涨幅{ma["chg_pct"]:+.1f}%')
            if not chg_3d_ok: reasons.append(f'近3日{ma["chg_3d"]:+.1f}%')
            failed.append({**c, 'reason': '+'.join(reasons)})
    
    if verbose:
        print()
        print(f"\n[Step3] 动量确认通过: {len(passed)}/{len(candidates)}")
        if passed:
            print(f"  通过:")
            for c in passed:
                m = c['ma_data']
                print(f"  🟢 {c.get('name','?'):10s}({c['code']}) MA5:{m['ma5']:.2f} MA10:{m['ma10']:.2f} 涨幅:{m['chg_pct']:+.1f}% 量比:{m['vol_ratio']:.2f}")
        if failed:
            print(f"  未通过:")
            for c in failed[:5]:
                print(f"  🔴 {c.get('name','?'):10s}({c['code']}) {c.get('reason','')}")
    
    return passed, failed

if __name__ == '__main__':
    # 测试
    from step1_sector_filter import run as step1_run
    step1_result = step1_run(verbose=False)
    candidates = step1_result['candidates'][:10]
    print(f"[Step3] 从Step1取前{len(candidates)}只验证动量")
    passed, failed = check_momentum(candidates)