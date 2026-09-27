#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
缠论工具 v1.0 - K 线包含处理 + 分型识别 + 笔绘制
"""

import baostock as bs
import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ==================== 1. K 线包含处理 ====================

def process_kline_inclusion(klines):
    """
    K 线包含处理
    
    参数: klines = [{'high': h, 'low': l, 'open': o, 'close': c}, ...]
    返回：处理后的 K 线列表
    """
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
            
            # 判断方向
            if len(processed) >= 2:
                direction = 1 if processed[-1]['high'] > processed[-2]['high'] else -1
            else:
                direction = 1 if curr['close'] > curr['open'] else -1
            
            # 包含处理
            if direction == 1:  # 向上
                new_high = max(prev['high'], curr['high'])
                new_low = max(prev['low'], curr['low'])
            else:  # 向下
                new_high = min(prev['high'], curr['high'])
                new_low = min(prev['low'], curr['low'])
            
            processed[-1] = {
                'high': new_high,
                'low': new_low,
                'open': prev['open'],
                'close': curr['close'],
                'volume': prev.get('volume', 0) + curr.get('volume', 0),
            }
        else:
            processed.append(curr.copy())
        
        i += 1
    
    return processed


# ==================== 2. 分型识别 ====================

def identify_fractals(klines):
    """
    识别顶分型和底分型
    
    返回：[{'index': i, 'type': 'top'/'bottom', 'price': p}, ...]
    """
    if len(klines) < 3:
        return []
    
    fractals = []
    
    for i in range(1, len(klines) - 1):
        prev = klines[i-1]
        curr = klines[i]
        next_k = klines[i+1]
        
        # 顶分型：中间 K 线高点最高，低点也最高
        if curr['high'] > prev['high'] and curr['high'] > next_k['high'] and \
           curr['low'] > prev['low'] and curr['low'] > next_k['low']:
            fractals.append({
                'index': i,
                'type': 'top',
                'price': curr['high'],
                'low': curr['low'],
            })
        
        # 底分型：中间 K 线高点最低，低点也最低
        elif curr['high'] < prev['high'] and curr['high'] < next_k['high'] and \
             curr['low'] < prev['low'] and curr['low'] < next_k['low']:
            fractals.append({
                'index': i,
                'type': 'bottom',
                'price': curr['low'],
                'high': curr['high'],
            })
    
    return fractals


# ==================== 3. 笔绘制 ====================

def draw_bi(fractals):
    """
    绘制笔（顶分型 + 底分型 = 一笔）
    
    规则:
    1. 顶分型和底分型之间至少 1 根独立 K 线
    2. 顶分型在上，底分型在下（向下笔）
    3. 底分型在下，顶分型在上（向上笔）
    
    返回：[{'start': i, 'end': j, 'type': 'up'/'down', 'start_price': p1, 'end_price': p2}, ...]
    """
    if len(fractals) < 2:
        return []
    
    bis = []
    
    i = 0
    while i < len(fractals) - 1:
        curr = fractals[i]
        next_f = fractals[i+1]
        
        # 跳过同类型分型
        if curr['type'] == next_f['type']:
            i += 1
            continue
        
        # 检查 K 线间隔（至少 1 根独立 K 线）
        if abs(next_f['index'] - curr['index']) < 2:
            i += 1
            continue
        
        # 确定笔的方向
        if curr['type'] == 'bottom' and next_f['type'] == 'top':
            bi_type = 'up'
            start_price = curr['price']
            end_price = next_f['price']
        else:
            bi_type = 'down'
            start_price = curr['price']
            end_price = next_f['price']
        
        bis.append({
            'start': curr['index'],
            'end': next_f['index'],
            'type': bi_type,
            'start_price': start_price,
            'end_price': end_price,
            'start_fractal': curr,
            'end_fractal': next_f,
        })
        
        i += 1
    
    return bis


# ==================== 4. 线段识别 ====================

def identify_segments(bis):
    """
    识别线段（至少 3 笔重叠 = 一线段）
    
    返回：[{'start': i, 'end': j, 'type': 'up'/'down', 'bis': [...]}, ...]
    """
    if len(bis) < 3:
        return []
    
    segments = []
    
    i = 0
    while i < len(bis) - 2:
        # 检查 3 笔
        bi1 = bis[i]
        bi2 = bis[i+1]
        bi3 = bis[i+2]
        
        # 检查方向交替
        if bi1['type'] != bi2['type'] and bi2['type'] != bi3['type']:
            # 检查重叠
            if bi1['type'] == 'up':
                # 向上线段：第 3 笔高点超过第 1 笔高点
                if bi3['end_price'] > bi1['end_price']:
                    segments.append({
                        'start': bi1['start'],
                        'end': bi3['end'],
                        'type': 'up',
                        'bis': [bi1, bi2, bi3],
                    })
                    i += 3
                    continue
            else:
                # 向下线段：第 3 笔低点低于第 1 笔低点
                if bi3['end_price'] < bi1['end_price']:
                    segments.append({
                        'start': bi1['start'],
                        'end': bi3['end'],
                        'type': 'down',
                        'bis': [bi1, bi2, bi3],
                    })
                    i += 3
                    continue
        
        i += 1
    
    return segments


# ==================== 5. 中枢绘制 ====================

def draw_zhongshu(segments):
    """
    绘制中枢（至少 3 个连续线段的重叠区间）
    
    返回：[{'start': i, 'end': j, 'high': h, 'low': l, 'segments': [...]}, ...]
    """
    if len(segments) < 3:
        return []
    
    zhongshus = []
    
    i = 0
    while i < len(segments) - 2:
        seg1 = segments[i]
        seg2 = segments[i+1]
        seg3 = segments[i+2]
        
        # 计算重叠区间
        seg1_high = max(seg1['bis'][0]['end_price'], seg1['bis'][-1]['end_price'])
        seg1_low = min(seg1['bis'][0]['start_price'], seg1['bis'][-1]['start_price'])
        
        seg2_high = max(seg2['bis'][0]['end_price'], seg2['bis'][-1]['end_price'])
        seg2_low = min(seg2['bis'][0]['start_price'], seg2['bis'][-1]['start_price'])
        
        seg3_high = max(seg3['bis'][0]['end_price'], seg3['bis'][-1]['end_price'])
        seg3_low = min(seg3['bis'][0]['start_price'], seg3['bis'][-1]['start_price'])
        
        # 重叠区间
        zhongshu_high = min(seg1_high, seg2_high, seg3_high)
        zhongshu_low = max(seg1_low, seg2_low, seg3_low)
        
        if zhongshu_high > zhongshu_low:
            zhongshus.append({
                'start': seg1['start'],
                'end': seg3['end'],
                'high': zhongshu_high,
                'low': zhongshu_low,
                'segments': [seg1, seg2, seg3],
            })
            i += 3
        else:
            i += 1
    
    return zhongshus


# ==================== 主程序 ====================

def analyze_chan(code, name, start_date='2025-01-01', end_date='2026-03-08'):
    """
    缠论分析主函数
    """
    print(f"\n{'='*80}")
    print(f"缠论分析：{code} {name}")
    print(f"{'='*80}")
    
    # 获取日线数据
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
    
    if len(data) < 30:
        print("数据不足")
        return None
    
    print(f"获取数据：{len(data)} 条 K 线")
    
    # Step 1: K 线包含处理
    print("\nStep 1: K 线包含处理...")
    processed = process_kline_inclusion(data)
    print(f"  原始 K 线：{len(data)} 条")
    print(f"  处理后：{len(processed)} 条")
    
    # Step 2: 分型识别
    print("\nStep 2: 分型识别...")
    fractals = identify_fractals(processed)
    top_fractals = [f for f in fractals if f['type'] == 'top']
    bottom_fractals = [f for f in fractals if f['type'] == 'bottom']
    print(f"  顶分型：{len(top_fractals)} 个")
    print(f"  底分型：{len(bottom_fractals)} 个")
    
    # Step 3: 笔绘制
    print("\nStep 3: 笔绘制...")
    bis = draw_bi(fractals)
    up_bis = [b for b in bis if b['type'] == 'up']
    down_bis = [b for b in bis if b['type'] == 'down']
    print(f"  总笔数：{len(bis)} 笔")
    print(f"  向上笔：{len(up_bis)} 笔")
    print(f"  向下笔：{len(down_bis)} 笔")
    
    # Step 4: 线段识别
    print("\nStep 4: 线段识别...")
    segments = identify_segments(bis)
    up_segments = [s for s in segments if s['type'] == 'up']
    down_segments = [s for s in segments if s['type'] == 'down']
    print(f"  总线段：{len(segments)} 个")
    print(f"  向上线段：{len(up_segments)} 个")
    print(f"  向下线段：{len(down_segments)} 个")
    
    # Step 5: 中枢绘制
    print("\nStep 5: 中枢绘制...")
    zhongshus = draw_zhongshu(segments)
    print(f"  中枢数量：{len(zhongshus)} 个")
    
    # 输出结果
    print(f"\n{'='*80}")
    print("缠论分析结果:")
    print(f"{'='*80}")
    
    if segments:
        last_seg = segments[-1]
        print(f"当前线段：{last_seg['type'].upper()} 线段")
        print(f"  起点：{last_seg['start']}")
        print(f"  终点：{last_seg['end']}")
    
    if zhongshus:
        last_zs = zhongshus[-1]
        print(f"\n最近中枢:")
        print(f"  区间：[{last_zs['low']:.2f}, {last_zs['high']:.2f}]")
        print(f"  方向：{'向上' if last_zs['segments'][0]['type'] == 'up' else '向下'}")
    
    # 返回结构化数据
    return {
        'code': code,
        'name': name,
        'data': data,
        'processed': processed,
        'fractals': fractals,
        'bis': bis,
        'segments': segments,
        'zhongshus': zhongshus,
        'last_segment': segments[-1] if segments else None,
        'last_zhongshu': zhongshus[-1] if zhongshus else None,
    }


# ==================== 测试 ====================

if __name__ == '__main__':
    # 登录
    lg = bs.login()
    print(f"登录：{lg.error_msg}")
    
    # 测试股票
    test_stocks = [
        ('sh.600519', '贵州茅台'),
        ('sz.300750', '宁德时代'),
        ('sh.600276', '恒瑞医药'),
    ]
    
    results = []
    for code, name in test_stocks:
        result = analyze_chan(code, name)
        if result:
            results.append(result)
    
    # 总结
    print(f"\n{'='*80}")
    print("缠论分析总结:")
    print(f"{'='*80}")
    
    for r in results:
        seg_dir = r['last_segment']['type'] if r['last_segment'] else '无'
        zs_dir = r['last_zhongshu']['segments'][0]['type'] if r['last_zhongshu'] else '无'
        print(f"{r['code']} {r['name']}: 线段={seg_dir}, 中枢方向={zs_dir}")
    
    bs.logout()
    print(f"\n{'='*80}")
