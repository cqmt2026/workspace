# -*- coding: utf-8 -*-
"""
技术分析深化模块 v1.0
包含：MACD背离、KDJ超买超卖、缠论三类买卖点精确定义
"""

import efinance as ef
import pandas as pd
import numpy as np
import urllib.request


# ============ 数据获取 ============
def get_stock_data(code, days=120):
    """获取股票数据"""
    try:
        df = ef.stock.get_quote_history(code)
        if df is None or len(df) == 0:
            return None
        df = df.tail(days).copy()
        df.columns = [c.strip() for c in df.columns]
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期').reset_index(drop=True)
        return df
    except:
        return None


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


# ============ MACD背离 ============
def calculate_macd(df, fast=12, slow=26, signal=9):
    """计算MACD"""
    df = df.copy()
    df['EMA12'] = df['收盘'].ewm(span=fast, adjust=False).mean()
    df['EMA26'] = df['收盘'].ewm(span=slow, adjust=False).mean()
    df['DIF'] = df['EMA12'] - df['EMA26']
    df['DEA'] = df['DIF'].ewm(span=signal, adjust=False).mean()
    df['MACD'] = (df['DIF'] - df['DEA']) * 2
    return df


def find_macd_divergence(df, lookback=60):
    """
    识别MACD背离
    
    顶背离：价格创新高，MACD没创新高 → 卖出信号
    底背离：价格创新低，MACD没创新低 → 买入信号
    """
    df = df.tail(lookback).copy()
    
    divergences = []
    
    # 找最近的高点（窗口内）
    window = 10
    for i in range(window, len(df) - window):
        # 检查是否是局部高点
        left = df.iloc[i-window:i]
        right = df.iloc[i:i+window]
        current = df.iloc[i]
        
        # 局部高点判断
        is_high = (current['最高'] >= left['最高'].max() and 
                   current['最高'] >= right['最高'].max())
        
        if is_high:
            # 查找前一个高点
            prev_highs = df.iloc[:i].tail(window)
            if len(prev_highs) > 0:
                prev_max_idx = prev_highs['最高'].idxmax()
                prev_max_price = prev_highs.loc[prev_max_idx, '最高']
                prev_max_macd = df.loc[prev_max_idx, 'MACD']
                
                # 背离判断：价格创新高但MACD没创新高
                if current['MACD'] < prev_max_macd and current['最高'] > prev_max_price:
                    divergences.append({
                        'type': 'top',
                        'date': current['日期'],
                        'price': current['最高'],
                        'macd': current['MACD'],
                        'prev_price': prev_max_price,
                        'prev_macd': prev_max_macd
                    })
    
    return divergences


def analyze_macd_advanced(df):
    """MACD高级分析"""
    print(f"\n{'='*55}")
    print("📈 MACD深化：背离判断")
    print(f"{'='*55}")
    
    df = calculate_macd(df)
    latest = df.iloc[-1]
    
    print(f"\n  【当前状态】")
    print(f"  DIF: {latest['DIF']:.3f}")
    print(f"  DEA: {latest['DEA']:.3f}")
    print(f"  MACD柱: {latest['MACD']:.3f}")
    
    # 背离检测
    divs = find_macd_divergence(df, 60)
    
    print(f"\n  【背离检测】")
    if len(divs) == 0:
        print(f"  ✅ 近60日无背离信号")
    else:
        for div in divs[-3:]:  # 最近3个
            date = div['date'].strftime('%Y-%m-%d')
            print(f"  ⚠️ {date}: 顶背离")
            print(f"      价格: {div['price']:.2f} (前高{div['prev_price']:.2f})")
            print(f"      MACD: {div['macd']:.3f} (前高MACD{div['prev_macd']:.3f})")
    
    print(f"\n  【背离信号说明】")
    print(f"  顶背离：价格创新高，但MACD没创新高 → 警惕回调")
    print(f"  底背离：价格创新低，但MACD没创新低 → 关注抄底")
    
    return divs


# ============ KDJ超买超卖 ============
def calculate_kdj(df, n=9, m1=3, m2=3):
    """计算KDJ"""
    df = df.copy()
    low_n = df['最低'].rolling(window=n, min_periods=1).min()
    high_n = df['最高'].rolling(window=n, min_periods=1).max()
    rsv = (df['收盘'] - low_n) / (high_n - low_n) * 100
    rsv = rsv.fillna(50)
    df['K'] = rsv.ewm(alpha=1/m1, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/m2, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    return df


def analyze_kdj_advanced(df):
    """KDJ高级分析：超买超卖"""
    print(f"\n{'='*55}")
    print("📉 KDJ深化：超买超卖")
    print(f"{'='*55}")
    
    df = calculate_kdj(df)
    latest = df.iloc[-1]
    
    k = latest['K']
    d = latest['D']
    j = latest['J']
    
    print(f"\n  【当前值】")
    print(f"  K: {k:.1f} | D: {d:.1f} | J: {j:.1f}")
    
    # 超买超卖判断
    print(f"\n  【超买超卖区间】")
    print(f"  🔴 K>80: 超买区，警惕回调")
    print(f"  🟢 K<20: 超卖区，关注反弹")
    print(f"  ➡️ K在20-80之间: 正常区间")
    
    # 当前状态
    print(f"\n  【当前状态判断】")
    if k > 80:
        print(f"  ⚠️ K={k:.1f} > 80，当前处于【超买区】")
        print(f"  建议: 考虑减仓或观望")
    elif k < 20:
        print(f"  💡 K={k:.1f} < 20，当前处于【超卖区】")
        print(f"  建议: 关注反弹机会")
    elif k > 70:
        print(f"  ⚠️ K={k:.1f} > 70，接近超买")
        print(f"  建议: 谨慎追高")
    elif k < 30:
        print(f"  💡 K={k:.1f} < 30，接近超卖")
        print(f"  建议: 关注企稳信号")
    else:
        print(f"  ✅ K={k:.1f}，正常区间")
    
    # J值辅助
    print(f"\n  【J值辅助判断】")
    if j > 100:
        print(f"  ⚠️ J={j:.1f}>100，极端超买，警惕主力砸盘")
    elif j < 0:
        print(f"  💡 J={j:.1f}<0，极端超卖，反弹概率大")
    elif j > 90:
        print(f"  ⚠️ J={j:.1f}>90，超买信号")
    elif j < 10:
        print(f"  💡 J={j:.1f}<10，超卖信号")
    else:
        print(f"  ✅ J={j:.1f}，正常")


# ============ 缠论三类买卖点 ============
def chanlun_buy_sell_points(code, name=None):
    """缠论三类买卖点精确定义"""
    
    print(f"\n{'='*55}")
    print(f"🏛️ 缠论三类买卖点精确定义")
    print(f"{'='*55}")
    
    print(f"""
    【第一类买点（一买）】
    定义：下跌趋势背驰后的底部
    条件：
    1. 明显的下降趋势
    2. 价格创新低，但MACD/KDJ没创新低（背驰）
    3. 出现底分型确认
    
    特征：高风险高收益，是抄底的点
    风险：可能继续创新低，需要严格止损
    
    【第二类买点（二买）】
    定义：一买之后的回调不破新低
    条件：
    1. 已经出现一买
    2. 回调过程中价格不创新低
    3. 在回调低点形成底分型
    
    特征：相对安全，是较好的入场点
    优势：比一买确定性高，比三买位置好
    
    【第三类买点（三买）】
    定义：突破中枢后回踩不破中枢上沿
    条件：
    1. 已经形成中枢
    2. 价格突破中枢上沿
    3. 回踩时不跌破中枢上沿
    
    特征：趋势确认后的最佳入场点
    优势：趋势明确，假突破概率低
    
    【三类卖点（与买卖点相反）】
    一卖：上升趋势背驰后的顶部
    二卖：反弹不创新高
    三卖：跌破中枢后反抽不过中轨
    """)
    
    print(f"{'='*55}")
    print("📋 实战应用对照表")
    print(f"{'='*55}")
    
    # 获取当前持仓分析
    df = get_stock_data(code, 120)
    if df is not None:
        current_price, prev_close = get_realtime_price(code)
        if current_price:
            latest = df.iloc[-1]
            df = calculate_macd(df)
            df = calculate_kdj(df)
            
            k = df.iloc[-1]['K']
            dif = df.iloc[-1]['DIF']
            dea = df.iloc[-1]['DEA']
            
            print(f"""
    当前股票：{name or code} ({code})
    当前价格：{current_price:.2f}
    
    对照检查：
    ☐ 是否在下降趋势？→ {'是' if current_price < df['收盘'].mean() else '否'}
    ☐ 价格是否创新低？→ 近120日最低: {df['最低'].min():.2f}
    ☐ KDJ是否超卖？→ K={k:.1f} {'(超卖)' if k < 20 else '(正常)'}
    ☐ MACD是否背离？→ 需要对比前后高点
    ☐ 是否形成中枢？→ 需要观察笔的重叠
    
    【初步判断】
    """)
            
            if k < 30:
                print(f"    KDJ接近超卖，可能存在反弹机会")
            if dif > 0 and dea > 0:
                print(f"    MACD在零轴上方，中期趋势偏强")
    
    print(f"""
    【操作建议】
    • 一买（抄底）：高风险，不建议现在操作
    • 二买（回调买入）：等待回调低点
    • 三买（突破买入）：等待突破确认后再买
    """)


def full_analysis(code, name=None):
    """完整技术分析"""
    print(f"\n{'#'*55}")
    print(f"#  技术分析深化 - {name or code} ({code})")
    print(f"{'#'*55}")
    
    # 获取数据
    df = get_stock_data(code, 120)
    if df is None:
        print("⚠️ 数据获取失败")
        return
    
    current_price, prev_close = get_realtime_price(code)
    if current_price:
        print(f"\n💰 最新价: {current_price:.2f} (昨收: {prev_close:.2f})")
        df.iloc[-1, df.columns.get_loc('收盘')] = current_price
    
    # 1. MACD背离
    divs = analyze_macd_advanced(df)
    
    # 2. KDJ超买超卖
    analyze_kdj_advanced(df)
    
    # 3. 缠论三类买卖点
    chanlun_buy_sell_points(code, name)


if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "600549"
    name = sys.argv[2] if len(sys.argv) > 2 else "厦门钨业"
    full_analysis(code, name)
