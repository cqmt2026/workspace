# -*- coding: utf-8 -*-
"""
技术分析模块 v1.0
数据源：efinance（稳定）
包含：MACD、KDJ、均线、趋势判断
"""

import efinance as ef
import pandas as pd
import numpy as np
import urllib.request

# ============ 数据获取 ============
def get_stock_data(code, days=60):
    """获取股票历史数据（efinance）"""
    try:
        df = ef.stock.get_quote_history(code)
        if df is None or len(df) == 0:
            return None
        df = df.tail(days).copy()
        # 标准化列名
        df.columns = [c.strip() for c in df.columns]
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期')
        return df
    except Exception as e:
        print(f"获取数据失败: {e}")
        return None


def get_realtime_price(code):
    """获取实时价格（腾讯）"""
    url = f'https://qt.gtimg.cn/q=sh{code}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode('gbk')
    
    for line in data.splitlines():
        if f'sh{code}' in line:
            parts = line.split('~')
            return float(parts[3]), float(parts[4])  # 现价, 昨收
    return None, None


# ============ MACD 指标 ============
def calculate_macd(df, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    df = df.copy()
    
    df['EMA12'] = df['收盘'].ewm(span=fast, adjust=False).mean()
    df['EMA26'] = df['收盘'].ewm(span=slow, adjust=False).mean()
    df['DIF'] = df['EMA12'] - df['EMA26']
    df['DEA'] = df['DIF'].ewm(span=signal, adjust=False).mean()
    df['MACD'] = (df['DIF'] - df['DEA']) * 2
    
    return df


def analyze_macd(df):
    """分析MACD信号"""
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    dif = latest['DIF']
    dea = latest['DEA']
    dif_prev = prev['DIF']
    dea_prev = prev['DEA']
    
    # 交叉判断
    if dif > dea:
        cross = "🟢 金叉" if dif_prev <= dea_prev else "➡️ 多头排列"
    else:
        cross = "🔴 死叉" if dif_prev >= dea_prev else "➡️ 空头排列"
    
    signal = []
    signal.append(f"MACD状态: {cross}")
    signal.append(f"DIF: {dif:.3f} | DEA: {dea:.3f}")
    
    # MACD柱
    macd_bar = latest['MACD']
    if macd_bar > 0:
        signal.append(f"MACD柱: 红色（多头），力度 {macd_bar:.3f}")
    else:
        signal.append(f"MACD柱: 绿色（空头），力度 {abs(macd_bar):.3f}")
    
    # 零轴判断
    if dif > 0 and dea > 0:
        signal.append("中期趋势: 🟢 偏强（零轴上方）")
    elif dif < 0 and dea < 0:
        signal.append("中期趋势: 🔴 偏弱（零轴下方）")
    else:
        signal.append("中期趋势: 🟡 震荡")
    
    return "\n  ".join(signal)


# ============ KDJ 指标 ============
def calculate_kdj(df, n=9, m1=3, m2=3):
    """计算KDJ指标"""
    df = df.copy()
    
    low_n = df['最低'].rolling(window=n, min_periods=1).min()
    high_n = df['最高'].rolling(window=n, min_periods=1).max()
    
    rsv = (df['收盘'] - low_n) / (high_n - low_n) * 100
    rsv = rsv.fillna(50)
    
    df['K'] = rsv.ewm(alpha=1/m1, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/m2, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    return df


def analyze_kdj(df):
    """分析KDJ信号"""
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    k = latest['K']
    d = latest['D']
    j = latest['J']
    k_prev = prev['K']
    d_prev = prev['D']
    
    # 超买超卖
    if k > 80:
        status = "🔴 超买区"
    elif k < 20:
        status = "🟢 超卖区"
    else:
        status = "➡️ 正常"
    
    # 交叉
    if k > d and k_prev <= d_prev:
        cross = "🟢 金叉"
    elif k < d and k_prev >= d_prev:
        cross = "🔴 死叉"
    elif k > d:
        cross = "➡️ 多头"
    else:
        cross = "➡️ 空头"
    
    signal = []
    signal.append(f"KDJ状态: {status}")
    signal.append(f"交叉: {cross} (K={k:.1f}, D={d:.1f}, J={j:.1f})")
    
    if j > 100:
        signal.append("⚠️ J值>100，警惕回调")
    elif j < 0:
        signal.append("⚠️ J值<0，警惕反弹")
    
    return "\n  ".join(signal)


# ============ 均线系统 ============
def calculate_ma(df, periods=[5, 10, 20, 60]):
    """计算均线"""
    df = df.copy()
    for period in periods:
        df[f'MA{period}'] = df['收盘'].rolling(window=period).mean()
    return df


def analyze_ma(df):
    """分析均线信号"""
    latest = df.iloc[-1]
    
    ma5 = latest.get('MA5', None)
    ma10 = latest.get('MA10', None)
    ma20 = latest.get('MA20', None)
    ma60 = latest.get('MA60', None)
    price = latest['收盘']
    
    signal = []
    
    # 排列判断
    if all(x is not None for x in [ma5, ma10, ma20]):
        if ma5 > ma10 > ma20:
            signal.append("均线多头排列（上升趋势）")
        elif ma5 < ma10 < ma20:
            signal.append("均线空头排列（下降趋势）")
        else:
            signal.append("均线混乱（震荡）")
    
    # 价格关系
    if ma5:
        dist = (price - ma5) / ma5 * 100
        signal.append(f"价格 vs MA5: {dist:+.2f}%")
    
    if ma20:
        if price > ma20:
            signal.append(f"MA20({ma20:.2f})为支撑")
        else:
            signal.append(f"MA20({ma20:.2f})为阻力")
    
    return "\n  ".join(signal)


# ============ 综合分析 ============
def technical_analysis(code, name=None):
    """综合技术分析"""
    print(f"\n{'='*60}")
    print(f"📊 技术分析: {name or code} ({code})")
    print(f"{'='*60}")
    
    # 获取数据
    df = get_stock_data(code, 60)
    if df is None or len(df) < 30:
        print("  ⚠️ 数据获取失败")
        return
    
    # 获取实时价格
    current_price, prev_close = get_realtime_price(code)
    if current_price:
        print(f"\n  💰 最新价: {current_price:.2f} (昨收: {prev_close:.2f})")
        df.iloc[-1, df.columns.get_loc('收盘')] = current_price
    
    # 计算指标
    df = calculate_macd(df)
    df = calculate_kdj(df)
    df = calculate_ma(df)
    
    # 输出分析
    print(f"\n{'─'*55}")
    print("📈 MACD指标")
    print(f"{'─'*55}")
    print(f"  {analyze_macd(df)}")
    
    print(f"\n{'─'*55}")
    print("📉 KDJ指标")  
    print(f"{'─'*55}")
    print(f"  {analyze_kdj(df)}")
    
    print(f"\n{'─'*55}")
    print("📊 均线系统")
    print(f"{'─'*55}")
    print(f"  {analyze_ma(df)}")
    
    # 综合建议
    latest = df.iloc[-1]
    print(f"\n{'='*60}")
    print("💡 综合建议")
    print(f"{'='*60}")
    
    signals = []
    
    if latest['DIF'] > latest['DEA']:
        signals.append("MACD多头")
    else:
        signals.append("MACD空头")
    
    if latest['K'] > latest['D']:
        signals.append("KDJ多头")
    else:
        signals.append("KDJ空头")
    
    ma5 = latest.get('MA5', 0)
    if ma5 and latest['收盘'] > ma5:
        signals.append("站稳MA5")
    else:
        signals.append("跌破MA5")
    
    bullish = sum(1 for s in signals if '多头' in s or '站稳' in s)
    
    print(f"  信号: {' / '.join(signals)}")
    print(f"  多头信号: {bullish}/3")
    
    if bullish >= 2:
        print(f"  结论: 🟢 偏多，可买入或持有")
    elif bullish == 1:
        print(f"  结论: 🟡 震荡，谨慎观望")
    else:
        print(f"  结论: 🔴 偏空，注意风险")


if __name__ == "__main__":
    technical_analysis("600549", "厦门钨业")
