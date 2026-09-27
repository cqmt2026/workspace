# -*- coding: utf-8 -*-
"""持仓综合评估 — 整合所有系统能力（修复版）"""
import sqlite3, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

WORK = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
DB = r'F:\market_data.db'
FD = os.path.join(WORK, r'data\factors.db')
PF = os.path.join(WORK, r'data\portfolio.json')

conn = sqlite3.connect(DB)
fconn = sqlite3.connect(FD)
pf = json.load(open(PF, 'r', encoding='utf-8'))

print('=' * 60)
print('  持仓综合评估 2026-07-10 10:30')
print('=' * 60)

# 读取交易历史
hist_path = os.path.join(WORK, r'data\trade_history.json')
histories = json.load(open(hist_path, 'r', encoding='utf-8')) if os.path.exists(hist_path) else []

for h in pf['holdings']:
    code_orig = h['code']
    code_db = 'sh.' + code_orig[2:] if code_orig.startswith('sh') else 'sz.' + code_orig[2:]
    name = h['name']
    buy_price = h['buy_price']
    shares = h['shares']
    cost = buy_price * shares
    
    # === 1. 行情数据 ===
    r10 = conn.execute('SELECT close FROM daily_k WHERE code=? AND date="2026-07-10"', (code_db,)).fetchone()
    r09 = conn.execute('SELECT close FROM daily_k WHERE code=? AND date="2026-07-09"', (code_db,)).fetchone()
    r03 = conn.execute('SELECT close FROM daily_k WHERE code=? AND date="2026-07-03"', (code_db,)).fetchone()
    
    current = r10[0] if r10 else r09[0]
    prev = r09[0] if r09 else current
    base = r03[0] if r03 else current
    
    p_chg_d = (current - prev) / prev * 100
    p_chg_7d = (current - base) / base * 100
    p_cost = (current - buy_price) / buy_price * 100
    profit_yuan = (current - buy_price) * shares
    
    # === 2. 因子数据 ===
    factors = fconn.execute(
        'SELECT factor_name, value FROM factors WHERE code=? AND date="2026-07-09" ORDER BY factor_name',
        (code_db,)
    ).fetchall()
    fm = {f[0]: f[1] for f in factors}
    
    # === 3. 止损线计算 ===
    stop_5 = buy_price * 0.95
    stop_15 = buy_price * 0.85
    if p_cost > 10:
        dyn_stop = buy_price * 0.97
    elif p_cost > 5:
        dyn_stop = buy_price * 0.96
    else:
        dyn_stop = stop_5
    
    # === 4. 信号评分（改进版）===
    score = 50  # 基准50分
    reasons = []
    
    # 动量 (±20分)
    ma5 = fm.get('ma_5', current)
    ma20 = fm.get('ma_20', current)
    ma60 = fm.get('ma_60', current)
    
    if current > ma5 > ma20 > ma60:
        score += 20
        reasons.append('均线多头排列 +20')
    elif current > ma5 > ma20:
        score += 15
        reasons.append('短期多头 +15')
    elif current > ma20:
        score += 5
        reasons.append('在20日均线上 +5')
    elif current > ma60:
        score += 0
        reasons.append('在60日均线上 0')
    else:
        score -= 20
        reasons.append('均线空头排列 -20')
    
    # 量能 (±15分)
    vol_ratio = fm.get('vol_ratio', 1)
    if vol_ratio and vol_ratio > 2:
        score += 15
        reasons.append(f'大幅放量(量比{vol_ratio:.2f}) +15')
    elif vol_ratio and vol_ratio > 1.5:
        score += 10
        reasons.append(f'放量(量比{vol_ratio:.2f}) +10')
    elif vol_ratio and vol_ratio > 1:
        score += 5
        reasons.append(f'温和放量(量比{vol_ratio:.2f}) +5')
    elif vol_ratio and vol_ratio < 0.5:
        score -= 10
        reasons.append(f'大幅缩量(量比{vol_ratio:.2f}) -10')
    elif vol_ratio and vol_ratio < 0.8:
        score -= 5
        reasons.append(f'缩量(量比{vol_ratio:.2f}) -5')
    else:
        reasons.append(f'量比正常(量比{vol_ratio:.2f}) 0')
    
    # RSI超买/超卖 (±15分)
    rsi = fm.get('rsi_14', 50)
    if rsi and rsi > 75:
        score -= 15
        reasons.append(f'RSI严重超买({rsi:.1f}) -15')
    elif rsi and rsi > 65:
        score -= 8
        reasons.append(f'RSI接近超买({rsi:.1f}) -8')
    elif rsi and rsi < 25:
        score += 15
        reasons.append(f'RSI严重超卖({rsi:.1f}) +15')
    elif rsi and rsi < 35:
        score += 8
        reasons.append(f'RSI接近超卖({rsi:.1f}) +8')
    else:
        reasons.append(f'RSI中性({rsi:.1f}) 0')
    
    # 5日涨幅过热/过冷 (±10分)
    p5d = fm.get('pct_chg_5d', 0)
    if p5d and p5d > 15:
        score -= 10
        reasons.append(f'5日涨{p5d:.1f}%过热 -10')
    elif p5d and p5d > 8:
        score -= 5
        reasons.append(f'5日涨{p5d:.1f}%偏高 -5')
    elif p5d and p5d < -15:
        score -= 10
        reasons.append(f'5日跌{p5d:.1f}%过冷 -10')
    elif p5d and p5d < -8:
        score -= 5
        reasons.append(f'5日跌{p5d:.1f}%偏低 -5')
    else:
        reasons.append(f'5日涨跌正常({p5d:+.1f}%) 0')
    
    # MACD金叉/死叉 (±10分)
    macd_cross = fm.get('macd_cross', 0)
    if macd_cross == 1:
        score += 10
        reasons.append('MACD金叉 +10')
    elif macd_cross == -1:
        score -= 10
        reasons.append('MACD死叉 -10')
    else:
        reasons.append('MACD中性 0')
    
    # 盈亏状态修正
    if p_cost < -10:
        score -= 15
        reasons.append('亏损>10% -15')
    elif p_cost > 15:
        score += 10
        reasons.append('盈利>15% +10')
    
    # === 5. 操作建议 ===
    advices = []
    
    # 止损建议
    if p_cost < -5 and p_chg_d < -2:
        advices.append('⚠️ 关注止损线')
    elif p_cost < -10:
        advices.append('🔴 考虑止损离场')
    
    # 获利了结建议
    if p_cost > 10 and rsi > 65:
        advices.append('🟡 RSI接近超买，考虑获利了结/减仓')
    
    # 趋势跟踪建议
    if score >= 65:
        advices.append('🟢 趋势良好，继续持有')
    elif score >= 45:
        advices.append('🟡 趋势一般，谨慎持有')
    else:
        advices.append('🔴 趋势偏弱，考虑减仓/止损')
    
    # 7日跌幅过大警告
    if p_chg_7d < -10:
        advices.append('🟡 7日跌幅较大，关注是否跌破关键支撑')
    
    # === 6. 输出 ===
    print(f'\n{"="*60}')
    print(f'  {name} ({code_orig})')
    print(f'{"="*60}')
    print(f'  持仓: {shares}股 @ {buy_price:.2f} (成本{cost:.0f}元)')
    print(f'  最新: {current:.2f} | 盈亏: {p_cost:+.2f}% ({profit_yuan:+.0f}元)')
    print(f'  日涨跌: {p_chg_d:+.2f}% | 7日: {p_chg_7d:+.2f}%')
    print(f'  止损: 5%={stop_5:.2f} | 15%={stop_15:.2f} | 动态={dyn_stop:.2f}')
    print(f'  信号评分: {score}/100')
    print(f'  评分详情: {", ".join(reasons)}')
    print(f'  建议: {"; ".join(advices)}')

# 汇总
print(f'\n{"="*60}')
print('  汇总')
print(f'{"="*60}')
total_cost = sum(h['shares'] * h['buy_price'] for h in pf['holdings'])
total_current = 0
for _h in pf['holdings']:
    _db = 'sh.' + _h['code'][2:] if _h['code'].startswith('sh') else 'sz.' + _h['code'][2:]
    r = conn.execute('SELECT close FROM daily_k WHERE code=? AND date="2026-07-10"', (_db,)).fetchone()
    if r:
        total_current += _h['shares'] * r[0]
total_p = (total_current - total_cost) / total_cost * 100
total_y = total_current - total_cost
print(f'  总成本: {total_cost:.0f}元')
print(f'  总市值: {total_current:.0f}元')
print(f'  总盈亏: {total_p:+.2f}% ({total_y:+.0f}元)')

conn.close()
fconn.close()