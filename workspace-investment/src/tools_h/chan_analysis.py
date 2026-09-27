#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chan Theory Analysis - All-in-One
缠论综合分析工具
"""

import baostock as bs
import sys

def calculate_macd(closes, fast=12, slow=26, signal=9):
    def ema(data, period):
        result = []
        multiplier = 2 / (period + 1)
        result.append(sum(data[:period]) / period)
        for val in data[period:]:
            result.append((val - result[-1]) * multiplier + result[-1])
        return result
    
    ema12 = ema(closes, fast)
    ema26 = ema(closes, slow)
    offset = slow - fast
    ema12 = ema12[offset:]
    dif = [e12 - e26 for e12, e26 in zip(ema12, ema26)]
    dea = ema(dif, signal)
    offset2 = len(dif) - len(dea)
    dif = dif[offset2:]
    macd_bar = [(d - e) * 2 for d, e in zip(dif, dea)]
    
    return {'dif': dif, 'dea': dea, 'macd': macd_bar}

def process_kline(klines):
    if len(klines) < 2:
        return klines
    processed = [klines[0].copy()]
    i = 1
    while i < len(klines):
        prev, curr = processed[-1], klines[i]
        if (curr['high'] >= prev['high'] and curr['low'] <= prev['low']) or (curr['high'] <= prev['high'] and curr['low'] >= prev['low']):
            direction = 1 if (len(processed) >= 2 and processed[-1]['high'] > processed[-2]['high']) else -1
            if direction == 1:
                new_high, new_low = max(prev['high'], curr['high']), max(prev['low'], curr['low'])
            else:
                new_high, new_low = min(prev['high'], curr['high']), min(prev['low'], curr['low'])
            processed[-1] = {'high': new_high, 'low': new_low, 'open': prev['open'], 'close': curr['close']}
        else:
            processed.append(curr.copy())
        i += 1
    return processed

def identify_fractals(klines):
    if len(klines) < 3:
        return []
    fractals = []
    for i in range(1, len(klines) - 1):
        prev, curr, next_k = klines[i-1], klines[i], klines[i+1]
        if curr['high'] > prev['high'] and curr['high'] > next_k['high'] and curr['low'] > prev['low'] and curr['low'] > next_k['low']:
            fractals.append({'index': i, 'type': 'top', 'price': curr['high']})
        elif curr['high'] < prev['high'] and curr['high'] < next_k['high'] and curr['low'] < prev['low'] and curr['low'] < next_k['low']:
            fractals.append({'index': i, 'type': 'bottom', 'price': curr['low']})
    return fractals

def draw_bi(fractals):
    if len(fractals) < 2:
        return []
    bis = []
    i = 0
    while i < len(fractals) - 1:
        curr, next_f = fractals[i], fractals[i+1]
        if curr['type'] != next_f['type'] and abs(next_f['index'] - curr['index']) >= 2:
            bi_type = 'up' if curr['type'] == 'bottom' else 'down'
            bis.append({'start': curr['index'], 'end': next_f['index'], 'type': bi_type, 'start_price': curr['price'], 'end_price': next_f['price']})
        i += 1
    return bis

def identify_segments(bis):
    if len(bis) < 3:
        return []
    segments = []
    i = 0
    while i < len(bis) - 2:
        bi1, bi2, bi3 = bis[i], bis[i+1], bis[i+2]
        if bi1['type'] != bi2['type'] and bi2['type'] != bi3['type']:
            if bi1['type'] == 'up' and bi3['end_price'] > bi1['end_price']:
                segments.append({'start': bi1['start'], 'end': bi3['end'], 'type': 'up', 'bis': [bi1, bi2, bi3]})
                i += 3
                continue
            elif bi1['type'] == 'down' and bi3['end_price'] < bi1['end_price']:
                segments.append({'start': bi1['start'], 'end': bi3['end'], 'type': 'down', 'bis': [bi1, bi2, bi3]})
                i += 3
                continue
        i += 1
    return segments

def draw_zhongshu(segments):
    if len(segments) < 3:
        return []
    zhongshus = []
    i = 0
    while i < len(segments) - 2:
        seg1, seg2, seg3 = segments[i], segments[i+1], segments[i+2]
        s1_high = max(seg1['bis'][0]['end_price'], seg1['bis'][-1]['end_price'])
        s1_low = min(seg1['bis'][0]['start_price'], seg1['bis'][-1]['start_price'])
        s2_high = max(seg2['bis'][0]['end_price'], seg2['bis'][-1]['end_price'])
        s2_low = min(seg2['bis'][0]['start_price'], seg2['bis'][-1]['start_price'])
        s3_high = max(seg3['bis'][0]['end_price'], seg3['bis'][-1]['end_price'])
        s3_low = min(seg3['bis'][0]['start_price'], seg3['bis'][-1]['start_price'])
        zs_high, zs_low = min(s1_high, s2_high, s3_high), max(s1_low, s2_low, s3_low)
        if zs_high > zs_low:
            zhongshus.append({'start': seg1['start'], 'end': seg3['end'], 'high': zs_high, 'low': zs_low, 'segments': [seg1, seg2, seg3]})
            i += 3
        else:
            i += 1
    return zhongshus

def detect_beichi(segments, macd_data):
    if len(segments) < 2 or not macd_data:
        return []
    beichis = []
    macd_bars = macd_data['macd']
    for i in range(len(segments) - 2):
        seg1, seg3 = segments[i], segments[i+2]
        if seg1['type'] == seg3['type']:
            start1, end1 = min(seg1['start'], seg1['end']), max(seg1['start'], seg1['end'])
            start3, end3 = min(seg3['start'], seg3['end']), max(seg3['start'], seg3['end'])
            if start1 >= len(macd_bars) or start3 >= len(macd_bars):
                continue
            area1 = sum(abs(macd_bars[j]) for j in range(start1, min(end1, len(macd_bars))) if (macd_bars[j] > 0 if seg1['type'] == 'up' else macd_bars[j] < 0))
            area3 = sum(abs(macd_bars[j]) for j in range(start3, min(end3, len(macd_bars))) if (macd_bars[j] > 0 if seg3['type'] == 'up' else macd_bars[j] < 0))
            seg1_price = seg1['bis'][-1]['end_price'] if seg1.get('bis') else seg1['end_price'] if 'end_price' in seg1 else 0
            seg3_price = seg3['bis'][-1]['end_price'] if seg3.get('bis') else seg3['end_price'] if 'end_price' in seg3 else 0
            if seg1['type'] == 'up' and seg3_price > seg1_price and area1 > 0 and area3 < area1 * 0.7:
                beichis.append({'type': 'top', 'price': seg3_price, 'reduce': round((area1 - area3) / area1, 3)})
            elif seg1['type'] == 'down' and seg3_price < seg1_price and area1 > 0 and area3 < area1 * 0.7:
                beichis.append({'type': 'bottom', 'price': seg3_price, 'reduce': round((area1 - area3) / area1, 3)})
    return beichis

def analyze(code, name):
    rs = bs.query_history_k_data_plus(code, 'date,open,high,low,close', start_date='2025-01-01', end_date='2026-03-08')
    data = []
    while rs.error_msg == 'success' and rs.next():
        row = rs.get_row_data()
        data.append({'open': float(row[1]), 'high': float(row[2]), 'low': float(row[3]), 'close': float(row[4])})
    
    if len(data) < 60:
        return None
    
    processed = process_kline(data)
    fractals = identify_fractals(processed)
    bis = draw_bi(fractals)
    segments = identify_segments(bis)
    zhongshus = draw_zhongshu(segments)
    closes = [d['close'] for d in processed]
    macd_data = calculate_macd(closes)
    beichis = detect_beichi(segments, macd_data)
    
    return {
        'code': code, 'name': name,
        'segments': segments, 'zhongshus': zhongshus, 'beichis': beichis,
        'last_seg': segments[-1] if segments else None,
        'last_zs': zhongshus[-1] if zhongshus else None,
    }

if __name__ == '__main__':
    lg = bs.login()
    print(f"Login: {lg.error_msg}")
    
    stocks = [('sh.600519', 'Guizhou Moutai'), ('sz.300750', 'CATL'), ('sh.600276', 'Hengrui Pharma')]
    results = [analyze(c, n) for c, n in stocks]
    results = [r for r in results if r]
    
    print(f"\n{'='*60}")
    print("Chan Theory Analysis Summary")
    print(f"{'='*60}")
    for r in results:
        seg = r['last_seg']['type'] if r['last_seg'] else 'None'
        zs = f"[{r['last_zs']['low']:.0f}, {r['last_zs']['high']:.0f}]" if r['last_zs'] else 'None'
        beichi = len(r['beichis'])
        print(f"{r['code']}: Segment={seg}, ZS={zs}, Beichi={beichi}")
    
    bs.logout()
