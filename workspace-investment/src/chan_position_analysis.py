# -*- coding: utf-8 -*-
"""
缠论持仓分析 - 针对当前持仓个股
厦门钨业(600549.SH) + 粤电力A(000539.SZ)
"""
import baostock as bs
import json
import sys
from datetime import datetime, timedelta

# 登录baostock
lg = bs.login()
print('=' * 55)
print('  缠论持仓分析')
print('=' * 55)

# 持仓列表
positions = [
    {'code': 'sh.600549', 'name': '厦门钨业', 'shares': 900, 'cost': 63.20},
    {'code': 'sz.000539', 'name': '粤电力A', 'shares': 2800, 'cost': 6.16},
]

# 拉取近120天日K线
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

def get_kline(code):
    rs = bs.query_history_k_data_plus(
        code,
        'date,open,high,low,close,volume,amount',
        start_date=start_date, end_date=end_date,
        frequency='d', adjustflag='2'  # 前复权
    )
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    return data

def calc_ma(closes, period):
    """简单移动平均"""
    result = []
    for i in range(len(closes)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(closes[i-period+1:i+1]) / period)
    return result

def find_fenxing(klines, threshold=0.03):
    """
    识别分型（顶/底）
    顶分型：中间K线高点最高，低点也最高
    底分型：中间K线低点最低，高点也最低
    """
    fractals = []
    for i in range(1, len(klines) - 1):
        prev = klines[i-1]
        curr = klines[i]
        nxt = klines[i+1]
        curr_high = float(curr[2])
        curr_low = float(curr[3])
        prev_high = float(prev[2])
        prev_low = float(prev[3])
        next_high = float(nxt[2])
        next_low = float(nxt[3])
        
        # 顶分型
        if curr_high > prev_high and curr_high > next_high and curr_low > prev_low and curr_low > next_low:
            fractals.append({'i': i, 'type': 'top', 'high': curr_high, 'low': curr_low, 'date': curr[0]})
        # 底分型
        elif curr_low < prev_low and curr_low < next_low and curr_high < prev_high and curr_high < next_high:
            fractals.append({'i': i, 'type': 'bottom', 'high': curr_high, 'low': curr_low, 'date': curr[0]})
    return fractals

def analyze_chan(code_name, klines, cost):
    """缠论简化分析"""
    if len(klines) < 20:
        return None
    
    closes = [float(k[4]) for k in klines]
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    
    # 找分型
    fractals = find_fenxing(klines)
    
    # 找最近的笔（用分型搭建）
    # 简化：找最近一个顶分型和底分型，算幅度
    tops = [f for f in fractals if f['type'] == 'top']
    bottoms = [f for f in fractals if f['type'] == 'bottom']
    
    # 最近20根K线
    recent_k = klines[-20:]
    recent_closes = closes[-20:]
    recent_highs = highs[-20:]
    recent_lows = lows[-20:]
    
    cur_price = recent_closes[-1]
    cur_high = max(recent_highs)
    cur_low = min(recent_lows)
    
    # 均线
    ma5 = calc_ma(recent_closes, 5)
    ma10 = calc_ma(recent_closes, 10)
    ma20 = calc_ma(recent_closes, 20)
    
    ma5_val = ma5[-1] if ma5[-1] else 0
    ma10_val = ma10[-1] if ma10[-1] else 0
    ma20_val = ma20[-1] if ma20[-1] else 0
    
    # 趋势判断（用最近高低点）
    price_range = cur_high - cur_low
    from_low = (cur_price - cur_low) / cur_low * 100 if cur_low else 0
    
    # 找出最近的主要高低点
    recent_tops = [f for f in tops if f['i'] >= len(klines) - 20]
    recent_bottoms = [f for f in bottoms if f['i'] >= len(klines) - 20]
    
    # 计算从建仓成本到现在的变化
    cost_diff = (cur_price - cost) / cost * 100
    
    # 买卖信号（简化）
    signal = '观望'
    reason = []
    
    if tops and bottoms:
        last_top = tops[-1] if tops else None
        last_bottom = bottoms[-1] if bottoms else None
        
        if last_top and last_bottom:
            # 笔幅度
            if last_top['high'] > last_bottom['low']:
                swing = last_top['high'] - last_bottom['low']
                from_bottom_pct = (cur_price - last_bottom['low']) / last_bottom['low'] * 100
                from_top_pct = (last_top['high'] - cur_price) / last_top['high'] * 100
            else:
                swing = last_bottom['low'] - last_top['high']
                from_bottom_pct = (cur_price - last_top['high']) / last_top['high'] * 100
                from_top_pct = (last_bottom['low'] - cur_price) / last_bottom['low'] * 100
    
    # 均线多头/空头排列
    if ma5_val and ma10_val and ma20_val:
        if ma5_val > ma10_val > ma20_val:
            signal = '强势'
            reason.append('均线多头排列')
        elif ma5_val < ma10_val < ma20_val:
            signal = '弱势'
            reason.append('均线空头排列')
        else:
            signal = '震荡'
            reason.append('均线混乱')
    
    # 偏离成本
    if cost_diff > 10:
        reason.append('成本乖离大，注意止盈')
    elif cost_diff < -5:
        reason.append('跌破成本，注意止损')
    
    return {
        'cur_price': cur_price,
        'cur_high_20d': cur_high,
        'cur_low_20d': cur_low,
        'ma5': round(ma5_val, 2) if ma5_val else None,
        'ma10': round(ma10_val, 2) if ma10_val else None,
        'ma20': round(ma20_val, 2) if ma20_val else None,
        'signal': signal,
        'reason': reason,
        'cost_diff': round(cost_diff, 2),
        'fenxing_count': len(fractals),
        'last_top_date': tops[-1]['date'] if tops else None,
        'last_bottom_date': bottoms[-1]['date'] if bottoms else None,
    }

for pos in positions:
    print()
    print('=' * 55)
    print('  %s (%s)' % (pos['name'], pos['code']))
    print('  成本: %.2f  持仓: %d股' % (pos['cost'], pos['shares']))
    print('=' * 55)
    
    klines = get_kline(pos['code'])
    print('  K线数量: %d根' % len(klines))
    
    if len(klines) < 20:
        print('  数据不足，跳过')
        continue
    
    result = analyze_chan(pos['code'], klines, pos['cost'])
    
    print()
    print('  【缠论结构】')
    print('  分型数量: %d个' % result['fenxing_count'])
    print('  最近顶分型: %s' % (result['last_top_date'] or '无'))
    print('  最近底分型: %s' % (result['last_bottom_date'] or '无'))
    print()
    print('  【均线】')
    print('  MA5:  %.2f' % (result['ma5'] or 0))
    print('  MA10: %.2f' % (result['ma10'] or 0))
    print('  MA20: %.2f' % (result['ma20'] or 0))
    print()
    print('  【当前价格】')
    print('  现价:    %.2f' % result['cur_price'])
    print('  20日高:  %.2f' % result['cur_high_20d'])
    print('  20日低:  %.2f' % result['cur_low_20d'])
    print()
    print('  【偏离成本】')
    print('  当前 vs 成本: %+.2f%%' % result['cost_diff'])
    print()
    print('  【信号】')
    print('  状态: %s' % result['signal'])
    if result['reason']:
        for r in result['reason']:
            print('  - %s' % r)
    else:
        print('  - 无明显信号')

bs.logout()
print()
print('=' * 55)
print('  分析完成')
print('=' * 55)