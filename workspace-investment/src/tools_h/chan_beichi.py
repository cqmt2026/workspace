#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chan Theory Tools v2.0 - Beichi Detection + Buy/Sell Points
缠论工具 v2.0 - 背驰检测 + 买卖点识别
"""

import baostock as bs
import sys
import io

# Force UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Import from chan_tools
try:
    from chan_tools import process_kline_inclusion, identify_fractals, draw_bi, identify_segments, draw_zhongshu
except ImportError:
    print("Error: Cannot import chan_tools. Make sure it's in the same directory.")
    sys.exit(1)


# ==================== 6. MACD Calculation ====================

def calculate_macd(closes, fast=12, slow=26, signal=9):
    """
    Calculate MACD
    
    Returns: {'ema12': [...], 'ema26': [...], 'dif': [...], 'dea': [...], 'macd': [...]}
    """
    if len(closes) < slow + signal:
        return None
    
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
    
    return {
        'ema12': ema12,
        'ema26': ema26,
        'dif': dif,
        'dea': dea,
        'macd': macd_bar,
    }


# ==================== 7. Beichi (Divergence) Detection ====================

def detect_beichi(segments, macd_data):
    """
    Detect trend divergence (beichi)
    
    Conditions:
    1. Two same-direction centers
    2. Leaving segment makes new high/low
    3. MACD area decreases
    
    Returns: [{'type': 'top'/'bottom', 'index': i, 'price': p, 'macd_compare': {...}}, ...]
    """
    if len(segments) < 2 or not macd_data:
        return []
    
    beichis = []
    
    for i in range(len(segments) - 2):
        seg1 = segments[i]
        seg2 = segments[i+1]
        seg3 = segments[i+2]
        
        if seg1['type'] == seg3['type'] and seg1['type'] != seg2['type']:
            if seg1['type'] == 'up':
                if seg3['end_price'] > seg1['end_price']:
                    macd_area1 = calculate_macd_area(macd_data, seg1, negative=False)
                    macd_area3 = calculate_macd_area(macd_data, seg3, negative=False)
                    
                    if macd_area1 and macd_area3 and macd_area3 < macd_area1 * 0.7:
                        beichis.append({
                            'type': 'top',
                            'index': seg3['end'],
                            'price': seg3['end_price'],
                            'macd_compare': {
                                'area1': round(macd_area1, 2),
                                'area3': round(macd_area3, 2),
                                'reduce': round((macd_area1 - macd_area3) / macd_area1, 3),
                            },
                        })
            else:
                if seg3['end_price'] < seg1['end_price']:
                    macd_area1 = calculate_macd_area(macd_data, seg1, negative=True)
                    macd_area3 = calculate_macd_area(macd_data, seg3, negative=True)
                    
                    if macd_area1 and macd_area3 and macd_area3 < macd_area1 * 0.7:
                        beichis.append({
                            'type': 'bottom',
                            'index': seg3['end'],
                            'price': seg3['end_price'],
                            'macd_compare': {
                                'area1': round(macd_area1, 2),
                                'area3': round(macd_area3, 2),
                                'reduce': round((macd_area1 - macd_area3) / macd_area1, 3),
                            },
                        })
    
    return beichis


def calculate_macd_area(macd_data, segment, negative=False):
    """
    Calculate MACD bar area (red or green)
    """
    if not macd_data or 'macd' not in macd_data:
        return None
    
    macd_bars = macd_data['macd']
    start = min(segment['start'], segment['end'])
    end = max(segment['start'], segment['end'])
    
    if start >= len(macd_bars) or end >= len(macd_bars):
        return None
    
    area = 0
    for i in range(start, min(end, len(macd_bars))):
        if negative:
            if macd_bars[i] < 0:
                area += abs(macd_bars[i])
        else:
            if macd_bars[i] > 0:
                area += macd_bars[i]
    
    return area if area > 0 else None


# ==================== 8. Buy/Sell Points Identification ====================

def identify_buy_sell_points(segments, zhongshus, beichis):
    """
    Identify 1st, 2nd, 3rd buy/sell points
    
    Returns: [{'type': '1buy'/'2buy'/'3buy'/'1sell'/'2sell'/'3sell', 'index': i, 'price': p}, ...]
    """
    points = []
    
    # 1st buy/sell (beichi points)
    for beichi in beichis:
        if beichi['type'] == 'bottom':
            points.append({
                'type': '1buy',
                'index': beichi['index'],
                'price': beichi['price'],
                'confidence': 'high' if beichi['macd_compare']['reduce'] > 0.5 else 'medium',
            })
        else:
            points.append({
                'type': '1sell',
                'index': beichi['index'],
                'price': beichi['price'],
                'confidence': 'high' if beichi['macd_compare']['reduce'] > 0.5 else 'medium',
            })
    
    # 2nd buy/sell (pullback after 1st)
    for point in points:
        if point['type'] == '1buy':
            for seg in segments:
                if seg['start'] > point['index'] and seg['type'] == 'down':
                    if seg['end_price'] > point['price']:
                        points.append({
                            'type': '2buy',
                            'index': seg['end'],
                            'price': seg['end_price'],
                            'confidence': 'medium',
                        })
                        break
        
        elif point['type'] == '1sell':
            for seg in segments:
                if seg['start'] > point['index'] and seg['type'] == 'up':
                    if seg['end_price'] < point['price']:
                        points.append({
                            'type': '2sell',
                            'index': seg['end'],
                            'price': seg['end_price'],
                            'confidence': 'medium',
                        })
                        break
    
    # 3rd buy/sell (center breakout pullback)
    for zs in zhongshus:
        for seg in segments:
            if seg['end'] > zs['end']:
                if seg['type'] == 'up' and seg['end_price'] > zs['high']:
                    points.append({
                        'type': '3buy_watch',
                        'index': seg['end'],
                        'price': seg['end_price'],
                        'zhongshu_high': zs['high'],
                        'note': 'Wait for pullback not entering center',
                    })
                elif seg['type'] == 'down' and seg['end_price'] < zs['low']:
                    points.append({
                        'type': '3sell_watch',
                        'index': seg['end'],
                        'price': seg['end_price'],
                        'zhongshu_low': zs['low'],
                        'note': 'Wait for rebound not entering center',
                    })
    
    return points


# ==================== Main Analysis Function ====================

def analyze_chan_full(code, name, start_date='2025-01-01', end_date='2026-03-08'):
    """
    Full Chan theory analysis (with beichi and buy/sell points)
    """
    print(f"\n{'='*80}")
    print(f"Chan Analysis: {code} {name}")
    print(f"{'='*80}")
    
    # Get data
    rs = bs.query_history_k_data_plus(
        code,
        'date,open,high,low,close,volume',
        start_date=start_date,
        end_date=end_date
    )
    
    data = []
    while rs.error_msg == 'success' and rs.next():
        row = rs.get_row_data()
        data.append({
            'date': row[0],
            'open': float(row[1]),
            'high': float(row[2]),
            'low': float(row[3]),
            'close': float(row[4]),
            'volume': int(row[5]),
        })
    
    if len(data) < 60:
        print("Insufficient data")
        return None
    
    print(f"Data: {len(data)} candles")
    
    # Process
    processed = process_kline_inclusion(data)
    fractals = identify_fractals(processed)
    bis = draw_bi(fractals)
    segments = identify_segments(bis)
    zhongshus = draw_zhongshu(segments)
    
    print(f"Processed: {len(data)}->{len(processed)} | Fractals: {len(fractals)} | Bi: {len(bis)} | Seg: {len(segments)} | ZS: {len(zhongshus)}")
    
    # MACD
    closes = [d['close'] for d in processed]
    macd_data = calculate_macd(closes)
    
    if macd_data:
        print(f"MACD: DIF length={len(macd_data['dif'])}")
    
    # Beichi detection
    beichis = detect_beichi(segments, macd_data)
    print(f"\nBeichi: {len(beichis)} found")
    for b in beichis:
        print(f"  {b['type']} beichi @ {b['price']:.2f} (MACD reduced {b['macd_compare']['reduce']*100:.1f}%)")
    
    # Buy/Sell points
    points = identify_buy_sell_points(segments, zhongshus, beichis)
    print(f"\nBuy/Sell Points: {len(points)} found")
    
    buy_points = [p for p in points if 'buy' in p['type']]
    sell_points = [p for p in points if 'sell' in p['type']]
    
    print(f"  Buy: {len(buy_points)}")
    for p in buy_points[-3:]:
        print(f"    {p['type']}: {p['price']:.2f} (confidence: {p.get('confidence', '-')})")
    
    print(f"  Sell: {len(sell_points)}")
    for p in sell_points[-3:]:
        print(f"    {p['type']}: {p['price']:.2f} (confidence: {p.get('confidence', '-')})")
    
    return {
        'code': code,
        'name': name,
        'segments': segments,
        'zhongshus': zhongshus,
        'beichis': beichis,
        'buy_points': buy_points,
        'sell_points': sell_points,
        'last_segment': segments[-1] if segments else None,
        'last_zhongshu': zhongshus[-1] if zhongshus else None,
    }


# ==================== Test ====================

if __name__ == '__main__':
    lg = bs.login()
    print(f"Login: {lg.error_msg}")
    
    test_stocks = [
        ('sh.600519', 'Guizhou Moutai'),
        ('sz.300750', 'CATL'),
        ('sh.600276', 'Hengrui Pharma'),
    ]
    
    results = []
    for code, name in test_stocks:
        result = analyze_chan_full(code, name)
        if result:
            results.append(result)
    
    print(f"\n{'='*80}")
    print("Summary:")
    print(f"{'='*80}")
    
    for r in results:
        seg = r['last_segment']['type'] if r['last_segment'] else 'None'
        print(f"{r['code']} {r['name']}: Segment={seg}, Beichi={len(r['beichis'])}, Buy={len(r['buy_points'])}, Sell={len(r['sell_points'])}")
    
    bs.logout()
