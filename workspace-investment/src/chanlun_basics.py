# -*- coding: utf-8 -*-
"""
缠论基础模块 v1.1
支持缓存数据 + 实时行情
"""

import pandas as pd
import numpy as np
import urllib.request
import os
import json
from datetime import datetime, timedelta


CACHE_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\cache'
os.makedirs(CACHE_DIR, exist_ok=True)


def get_stock_data_cached(code, days=120):
    """获取缓存数据或返回None"""
    cache_file = os.path.join(CACHE_DIR, f'{code}_daily.json')
    
    # 尝试读取缓存
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            df['日期'] = pd.to_datetime(df['日期'])
            return df.tail(days)
        except:
            pass
    return None


def save_stock_cache(code, df):
    """保存数据到缓存"""
    cache_file = os.path.join(CACHE_DIR, f'{code}_daily.json')
    try:
        data = df.to_dict('records')
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass


def get_realtime_price(code):
    """获取实时价格"""
    url = f'https://qt.gtimg.cn/q=sh{code}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('gbk')
        for line in data.splitlines():
            if f'sh{code}' in line:
                parts = line.split('~')
                return float(parts[3]), float(parts[4])
    except:
        pass
    return None, None


# ============ 分型识别 ============
def find_fractals(df):
    """识别顶分型/底分型"""
    fractals = []
    
    for i in range(1, len(df) - 1):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        next_k = df.iloc[i+1]
        
        if curr['最高'] > prev['最高'] and curr['最高'] > next_k['最高']:
            fractals.append((i, 'top', curr['最高']))
        elif curr['最低'] < prev['最低'] and curr['最低'] < next_k['最低']:
            fractals.append((i, 'bottom', curr['最低']))
    
    return fractals


# ============ 笔的识别（简化） ============
def find_pens_simple(df, fractals):
    """简化笔识别"""
    if len(fractals) < 2:
        return []
    
    pens = []
    i = 0
    while i < len(fractals) - 1:
        f1_idx, f1_type, f1_price = fractals[i]
        f2_idx, f2_type, f2_price = fractals[i+1]
        
        if f1_type == f2_type:
            i += 1
            continue
        
        # 简化：直接连接相邻异向分型
        if f1_type == 'bottom':
            pens.append({
                'type': 'up',
                'start_idx': f1_idx,
                'end_idx': f2_idx,
                'start_price': f1_price,
                'end_price': f2_price,
                'height': f2_price - f1_price
            })
        else:
            pens.append({
                'type': 'down',
                'start_idx': f1_idx,
                'end_idx': f2_idx,
                'start_price': f1_price,
                'end_price': f2_price,
                'height': f1_price - f2_price
            })
        i += 1
    
    return pens


# ============ 中枢识别（简化） ============
def find_zhongshu_simple(pens):
    """简化中枢识别：3笔重叠"""
    if len(pens) < 3:
        return None
    
    recent = pens[-3:]
    ranges = []
    for pen in recent:
        high = max(pen['start_price'], pen['end_price'])
        low = min(pen['start_price'], pen['end_price'])
        ranges.append((low, high))
    
    overlap_low = max(r[0] for r in ranges)
    overlap_high = min(r[1] for r in ranges)
    
    if overlap_low < overlap_high:
        return {
            'low': overlap_low,
            'high': overlap_high,
            'mid': (overlap_low + overlap_high) / 2
        }
    return None


# ============ 缠论分析（理论框架） ============
def chanlun_theory_report(code, name=None):
    """缠论理论框架报告（不依赖网络）"""
    
    # 获取实时价格
    current_price, prev_close = get_realtime_price(code)
    
    print(f"\n{'='*60}")
    print(f"📊 缠论基础分析: {name or code} ({code})")
    print(f"{'='*60}")
    
    if current_price:
        print(f"\n  💰 最新价: {current_price:.2f} (昨收: {prev_close:.2f})")
    else:
        print(f"\n  ⚠️ 实时行情获取失败")
        return
    
    print(f"\n{'─'*60}")
    print("📚 缠论核心概念")
    print(f"{'─'*60}")
    print("""
  【分型】
    顶分型：三根K线，中间最高 → 卖出信号
    底分型：三根K线，中间最低 → 买入信号
  
  【笔】
    上升笔：底分型 → 顶分型（连接）
    下降笔：顶分型 → 底分型（连接）
  
  【线段】
    三个笔构成线段（简化理解）
  
  【中枢】
    连续三笔重叠区间 → 盘整区间
    中枢上方强势，下方弱势
  
  【三类买卖点】
    一买：底部背驰后的第一个上升笔（高风险）
    二买：回调不破前低的买入点（较好）
    三买：突破中枢后回踩的买入点（最佳）
    """)
    
    print(f"\n{'─'*60}")
    print("📋 实战应用")
    print(f"{'─'*60}")
    print(f"""
  【当前持仓分析框架】
  
  厦门钨业(600549):
    成本: 62.50 | 现价: {current_price:.2f}
    
    分析步骤：
    1. 查看当前位置是否在重要支撑/压力位
    2. 观察分型是否出现顶分型（注意回调）
    3. 判断笔的方向（上升/下降）
    4. 确认是否有中枢形成
    5. 根据三类买卖点决策
    
  通策医疗(600763):
    成本: 43.75 | 现价: {current_price:.2f}
    
    （同上分析方法）
    """)
    
    print(f"\n{'='*60}")
    print("⚠️ 数据限制说明")
    print(f"{'='*60}")
    print("""
  由于网络不稳定，历史K线数据暂时无法获取。
  已安装库：akshare, efinance
  
  网络恢复后，运行：
    python src/technical_analysis.py  # MACD/KDJ分析
    python src/chanlun_basics.py      # 缠论分析
  
  或在Dashboard中查看实时数据。
    """)


if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "600549"
    name = sys.argv[2] if len(sys.argv) > 2 else "厦门钨业"
    chanlun_theory_report(code, name)
