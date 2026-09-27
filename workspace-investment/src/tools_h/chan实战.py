# -*- coding: utf-8 -*-
"""
缠论实战分析脚本
基于 H盘 chan_tools.py 的逻辑，对厦门钨业和粤电力进行日线级别缠论分析
"""
import json
import sys

# 加载数据
with open(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\src\tools_h\chan_analyze_data.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

def parse_klines(raw_data):
    """解析K线数据"""
    klines = []
    for bar in raw_data:
        parts = bar.split(',')
        klines.append({
            'date': parts[0],
            'open': float(parts[1]),
            'close': float(parts[2]),
            'high': float(parts[3]),
            'low': float(parts[4]),
            'volume': float(parts[5]),
        })
    return klines

klines_xm = parse_klines(raw['XMTC'])
klines_yd = parse_klines(raw['YDL'])

# 只取最近60个交易日进行分析
klines_xm60 = klines_xm[-60:]
klines_yd60 = klines_yd[-60:]

# ======== 1. K线包含处理 ========
def process_inclusion(klines):
    """K线包含处理"""
    if len(klines) < 2:
        return klines
    processed = [klines[0].copy()]
    i = 1
    while i < len(klines):
        prev = processed[-1]
        curr = klines[i]
        # 判断是否包含
        if (curr['high'] >= prev['high'] and curr['low'] <= prev['low']) or \
           (curr['high'] <= prev['high'] and curr['low'] >= prev['low']):
            if len(processed) >= 2:
                direction = 1 if processed[-1]['high'] > processed[-2]['high'] else -1
            else:
                direction = 1 if curr['close'] > curr['open'] else -1
            if direction == 1:  # 向上
                new_high = max(prev['high'], curr['high'])
                new_low = max(prev['low'], curr['low'])
            else:  # 向下
                new_high = min(prev['high'], curr['high'])
                new_low = min(prev['low'], curr['low'])
            processed[-1] = {
                'high': new_high, 'low': new_low,
                'open': prev['open'], 'close': curr['close'],
                'volume': prev.get('volume', 0) + curr.get('volume', 0),
                'date': prev.get('date', '')
            }
        else:
            processed.append(curr.copy())
        i += 1
    return processed

# ======== 2. 分型识别 ========
def find_fractals(klines):
    """识别顶底分型"""
    fractals = []
    for i in range(1, len(klines) - 1):
        prev = klines[i-1]
        curr = klines[i]
        next_k = klines[i+1]
        # 顶分型
        if curr['high'] > prev['high'] and curr['high'] > next_k['high'] and \
           curr['low'] > prev['low'] and curr['low'] > next_k['low']:
            fractals.append({'i': i, 'type': 'top', 'price': curr['high'], 'low': curr['low'], 'date': curr.get('date', '')})
        # 底分型
        elif curr['high'] < prev['high'] and curr['high'] < next_k['high'] and \
             curr['low'] < prev['low'] and curr['low'] < next_k['low']:
            fractals.append({'i': i, 'type': 'bottom', 'price': curr['low'], 'high': curr['high'], 'date': curr.get('date', '')})
    return fractals

# ======== 3. 笔识别 ========
def find_bi(fractals):
    """从分型识别笔：顶分型后有底分型=向下笔；底分型后有顶分型=向上笔"""
    bi_list = []
    if len(fractals) < 2:
        return bi_list
    i = 0
    current_dir = None
    while i < len(fractals) - 1:
        f1 = fractals[i]
        f2 = fractals[i+1]
        # 至少间隔1根K线
        if f2['i'] - f1['i'] < 2:
            i += 1
            continue
        if f1['type'] == 'top' and f2['type'] == 'bottom':
            # 顶分型高于底分型 = 向下笔
            if current_dir != 'down':
                bi_list.append({'start': f1, 'end': f2, 'dir': 'down'})
                current_dir = 'down'
        elif f1['type'] == 'bottom' and f2['type'] == 'top':
            # 底分型低于顶分型 = 向上笔
            if current_dir != 'up':
                bi_list.append({'start': f1, 'end': f2, 'dir': 'up'})
                current_dir = 'up'
        i += 1
    return bi_list

# ======== 4. 线段识别（简化版）=======
def find_segment(bi_list, min_overlap=3):
    """3笔重叠=线段"""
    segments = []
    if len(bi_list) < 3:
        return segments
    i = 0
    while i <= len(bi_list) - 3:
        b1, b2, b3 = bi_list[i], bi_list[i+1], bi_list[i+2]
        # 三笔同方向+有重叠
        if b1['dir'] == b2['dir'] == b3['dir']:
            # 检查笔之间的重叠
            highs = [b1['start']['price'] if b1['dir'] == 'up' else b1['end']['price'],
                     b2['start']['price'], b2['end']['price'],
                     b3['start']['price'], b3['end']['price']]
            lows = [b1['start']['price'] if b1['dir'] == 'down' else b1['end']['price'],
                     b2['start']['price'], b2['end']['price'],
                     b3['start']['price'], b3['end']['price']]
            seg_high = max(highs)
            seg_low = min(lows)
            overlap = seg_high - seg_low
            if overlap >= seg_low * 0.02:  # 重叠幅度>2%
                segments.append({
                    'bi_index': (i, i+2),
                    'high': seg_high,
                    'low': seg_low,
                    'dir': b1['dir'],
                    'start_date': b1['start']['date'],
                    'end_date': b3['end']['date'],
                    'overlap': overlap
                })
        i += 1
    return segments

# ======== 5. 中枢识别（简化版）=======
def find_zhongshu(segments):
    """识别中枢：3段重叠区间"""
    zhongshu_list = []
    if len(segments) < 3:
        return zhongshu_list
    i = 0
    while i <= len(segments) - 3:
        s1, s2, s3 = segments[i], segments[i+1], segments[i+2]
        if s1['dir'] == s2['dir'] == s3['dir']:
            max_low = max(s1['low'], s2['low'], s3['low'])
            min_high = min(s1['high'], s2['high'], s3['high'])
            if max_low < min_high:  # 有重叠
                zhongshu_list.append({
                    'seg_index': (i, i+2),
                    'high': min_high,
                    'low': max_low,
                    'mid': (min_high + max_low) / 2,
                    'dir': s1['dir'],
                    'start': s1['start_date'],
                    'end': s3['end_date'],
                })
        i += 1
    return zhongshu_list

# ======== 6. MACD背驰分析 ========
def macd_analysis(klines):
    """计算MACD"""
    closes = [k['close'] for k in klines]
    # EMA
    def ema(data, n):
        k = 2/(n+1)
        r = [data[0]]
        for p in data[1:]: r.append(p*k + r[-1]*(1-k))
        return r
    if len(closes) < 26:
        return None, None, None
    e12 = ema(closes, 12)
    e26 = ema(closes, 26)
    dif = [e12[i] - e26[i] for i in range(len(closes))]
    dea = ema(dif, 9)
    hist = [2*(dif[i]-dea[i]) for i in range(len(dif))]
    return dif[-1], dea[-1], hist[-1], dif[-5], hist[-5], hist[-20] if len(hist) >= 20 else (None, None, None)

def analyze(name, klines):
    print('='*60)
    print(name)
    print('='*60)
    k60 = klines[-60:]
    print(f'分析区间: {k60[0]["date"]} ~ {k60[-1]["date"]} (60日)')
    print(f'最新价: {k60[-1]["close"]:.2f}')
    print()

    # 包含处理
    proc = process_inclusion(k60)
    print(f'包含处理后: {len(k60)} -> {len(proc)} 根K线')

    # 分型
    fr = find_fractals(proc)
    tops = [f for f in fr if f['type'] == 'top']
    bots = [f for f in fr if f['type'] == 'bottom']
    print(f'顶分型: {len(tops)}个 | 底分型: {len(bots)}个')
    if tops:
        print(f'  最近顶分型: {tops[-1]["date"]} 价格{tops[-1]["price"]:.2f}')
    if bots:
        print(f'  最近底分型: {bots[-1]["date"]} 价格{bots[-1]["price"]:.2f}')
    print()

    # 笔
    bi = find_bi(fr)
    print(f'笔: {len(bi)}个')
    up_bi = [b for b in bi if b['dir'] == 'up']
    dn_bi = [b for b in bi if b['dir'] == 'down']
    if up_bi:
        print(f'  向上笔: {len(up_bi)}个')
        print(f'    最近向上笔: {up_bi[-1]["start"]["date"]}~{up_bi[-1]["end"]["date"]}')
        print(f'    起始底分型: {up_bi[-1]["start"]["price"]:.2f} -> 终止顶分型: {up_bi[-1]["end"]["price"]:.2f}')
    if dn_bi:
        print(f'  向下笔: {len(dn_bi)}个')
        print(f'    最近向下笔: {dn_bi[-1]["start"]["date"]}~{dn_bi[-1]["end"]["date"]}')
        print(f'    起始顶分型: {dn_bi[-1]["start"]["price"]:.2f} -> 终止底分型: {dn_bi[-1]["end"]["price"]:.2f}')
    print()

    # 线段
    seg = find_segment(bi)
    print(f'线段: {len(seg)}个')
    if seg:
        last_seg = seg[-1]
        print(f'  最近线段: {last_seg["start_date"]}~{last_seg["end_date"]} ({last_seg["dir"]})')
        print(f'  范围: {last_seg["low"]:.2f} ~ {last_seg["high"]:.2f}')
    print()

    # 中枢
    zs = find_zhongshu(seg)
    print(f'中枢: {len(zs)}个')
    if zs:
        for z in zs[-2:]:
            print(f'  [{z["start"]}~{z["end"]}] {z["dir"]} 区间:{z["low"]:.2f}~{z["high"]:.2f} 中位:{z["mid"]:.2f}')
    else:
        print('  (近期无标准3段重叠中枢)')
    print()

    # MACD
    dif, dea, hist, dif5, hist5, hist20 = macd_analysis(k60)
    if dif is not None:
        print('MACD (日线):')
        print(f'  DIF: {dif:.4f} | DEA: {dea:.4f} | MACD柱: {hist:.4f}')
        trend = '金叉区域(红柱)' if dif > 0 and hist > 0 else '死叉区域(绿柱)' if dif < 0 and hist < 0 else '即将金叉' if dif < 0 and hist > 0 else '即将死叉'
        print(f'  状态: {trend}')
        if dif5 and hist5:
            chg = (hist - hist5) / abs(hist5) * 100 if hist5 != 0 else 0
            print(f'  红柱变化: {hist:.4f} vs 5日前{hist5:.4f} ({(chg):+.1f}%)')
    print()
    return tops, bots, bi, seg, zs

# 分析
tops_xm, bots_xm, bi_xm, seg_xm, zs_xm = analyze('厦门钨业 (600549)', klines_xm)
tops_yd, bots_yd, bi_yd, seg_yd, zs_yd = analyze('粤电力A (000539)', klines_yd)