# -*- coding: utf-8 -*-
import json

def analyze_chanlun(kline, name):
    if not kline:
        return f'{name}: 无数据'

    closes = [k['close'] for k in kline]
    highs = [k['high'] for k in kline]
    lows = [k['low'] for k in kline]

    n = min(20, len(kline))
    closes = closes[-n:]
    highs = highs[-n:]
    lows = lows[-n:]

    # 找顶分型和底分型
    tops = []
    bottoms = []
    for i in range(1, n-1):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            tops.append(i)
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            bottoms.append(i)

    last_price = closes[-1]
    ma5 = sum(closes[-5:]) / 5
    ma10 = sum(closes[-10:]) / 10
    ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else sum(closes) / len(closes)

    trend = '上升' if ma5 > ma10 > ma20 else ('下降' if ma5 < ma10 < ma20 else '横盘')

    last_top = tops[-1] if tops else None
    last_bottom = bottoms[-1] if bottoms else None

    # 简化中枢
    zhongshang_high = sorted(highs[-10:])[-3]
    zhongshang_low = sorted(lows[-10:])[2]

    if last_price > zhongshang_high:
        position = '中枢上方(偏强)'
    elif last_price < zhongshang_low:
        position = '中枢下方(偏弱)'
    else:
        position = '中枢内(震荡)'

    signal = '可以关注' if len(bottoms) > 0 and trend != '下降' else '观望'

    result = f'''
=== {name} 缠论分析 ===
最近收盘: {last_price:.2f}
趋势: {trend}
均线: MA5={ma5:.2f} MA10={ma10:.2f} MA20={ma20:.2f}
顶分型: {len(tops)}个 (最近第{last_top}天前)
底分型: {len(bottoms)}个 (最近第{last_bottom}天前)
中枢区间: [{zhongshang_low:.2f}, {zhongshang_high:.2f}]
当前位置: {position}
信号: {signal}
'''
    return result

# 分析
for code, name in [('600549', '厦门钨业'), ('300492', '华图山鼎')]:
    path = rf'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\cache\{code}_daily.json'
    with open(path, 'r', encoding='utf-8') as f:
        kline = json.load(f)
    print(analyze_chanlun(kline, name))