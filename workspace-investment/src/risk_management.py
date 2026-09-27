# -*- coding: utf-8 -*-
"""
股票投资风险管理框架 v1.0
结合腾讯实时行情 + akshare历史数据
"""

import akshare as ak
import json
import urllib.request
import time

# ============ 风险管理核心参数 ============
RISK_PARAMS = {
    "max_loss_per_trade": 0.08,      # 单笔最大亏损 8%
    "target_profit_loss_ratio": 2.0,  # 盈亏比目标 1:2
    "stop_loss_types": {
        "fixed": 0.05,               # 固定止损 5%
        "trailing": 0.03,            # 移动止损 3%
    }
}

# ============ 获取实时行情（腾讯） ============
def get_realtime_quote(codes):
    """腾讯实时行情，稳定快速"""
    url = 'https://qt.gtimg.cn/q=' + ','.join(codes)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode('gbk')
    
    quotes = {}
    for line in data.splitlines():
        for code in codes:
            if code in line:
                parts = line.split('~')
                if len(parts) > 35:
                    quotes[code] = {
                        'name': parts[1],
                        'price': float(parts[3]),
                        'prev_close': float(parts[4]),
                        'open': float(parts[5]),
                        'high': float(parts[33]),
                        'low': float(parts[34]),
                    }
    return quotes

# ============ 获取历史数据（akshare，重试） ============
def get_hist_data(code, days=30):
    """akshare历史K线，带重试"""
    for attempt in range(3):
        try:
            df = ak.stock_zh_a_hist(symbol=code, period='daily', adjust='qfq', 
                                   start_date='20260301', end_date='20260424')
            return df.tail(days)
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            else:
                return None
    return None

# ============ 分析单个持仓 ============
def analyze_position(code, name, shares, cost):
    """分析单个持仓的风险指标"""
    print(f"\n{'='*55}")
    print(f"  【{name}】({code})")
    print(f"{'='*55}")
    
    # 获取实时行情
    market_code = 'sh' + code
    quotes = get_realtime_quote([market_code])
    
    if market_code in quotes:
        q = quotes[market_code]
        current_price = q['price']
        prev_close = q['prev_close']
        high = q['high']
        low = q['low']
        chg_pct = (current_price / prev_close - 1) * 100
        
        print(f"  📊 行情:")
        print(f"     当前价: {current_price:.2f} | 昨收: {prev_close:.2f}")
        print(f"     涨跌: {chg_pct:+.2f}% | 最高: {high:.2f} | 最低: {low:.2f}")
    else:
        print(f"  ⚠️ 实时行情获取失败")
        return None
    
    # 获取历史数据用于20日位置
    df = get_hist_data(code, 30)
    
    cost_total = cost * shares
    market_total = current_price * shares
    profit = market_total - cost_total
    profit_pct = (current_price / cost - 1) * 100
    
    print(f"\n  💰 持仓:")
    print(f"     持股: {shares}股 | 成本: {cost:.2f}")
    print(f"     市值: {market_total:,.0f}元 | 盈亏: {profit:+,.0f}元 ({profit_pct:+.2f}%)")
    
    # ============ 止损分析 ============
    print(f"\n  🛡️ 止损分析:")
    
    fixed_stop = cost * (1 - RISK_PARAMS["stop_loss_types"]["fixed"])
    trailing_stop = current_price * (1 - RISK_PARAMS["stop_loss_types"]["trailing"])
    
    # 距离止损位的距离
    dist_to_fixed = (current_price - fixed_stop) / current_price * 100
    dist_to_trailing = 3.0  # 固定3%
    
    print(f"     固定止损(-5%): {fixed_stop:.2f} | 距今: {dist_to_fixed:.1f}%")
    print(f"     移动止损(-3%): {trailing_stop:.2f} | 距今: {dist_to_trailing:.1f}%")
    
    # 盈亏目标
    target_profit = cost * (1 + RISK_PARAMS["target_profit_loss_ratio"] * RISK_PARAMS["stop_loss_types"]["fixed"])
    dist_to_target = (target_profit - current_price) / current_price * 100
    print(f"     目标卖出(+10%): {target_profit:.2f} | 距今: {dist_to_target:.1f}%")
    
    # ============ 20日位置分析 ============
    if df is not None and len(df) > 5:
        high_20d = df['最高'].max()
        low_20d = df['最低'].min()
        position = (current_price - low_20d) / (high_20d - low_20d) * 100
        
        print(f"\n  📈 20日位置:")
        print(f"     20日高: {high_20d:.2f} | 20日低: {low_20d:.2f}")
        print(f"     所处位置: {position:.0f}%", end="")
        
        if position < 30:
            print(" 🟢 低位区（风险较低）")
        elif position < 70:
            print(" 🟡 中位区（注意观察）")
        else:
            print(" 🔴 高位区（注意风险）")
    else:
        print(f"\n  📈 20日位置: 数据获取失败")
    
    # ============ 风险评估 ============
    print(f"\n  ⚠️ 风险评估:")
    
    if profit_pct < 0:
        loss_ratio = abs(profit_pct) / RISK_PARAMS["stop_loss_types"]["fixed"] * 100
        print(f"     当前状态: ⚠️ 浮亏 {profit_pct:.2f}%")
        print(f"     已消耗止损空间: {loss_ratio:.0f}%")
        if loss_ratio > 80:
            print(f"     🚨 警告：接近止损线！建议关注！")
    else:
        print(f"     当前状态: ✅ 盈利 {profit_pct:.2f}%")
        print(f"     可持有，观察移动止损")
    
    return {
        'name': name,
        'code': code,
        'current_price': current_price,
        'profit_pct': profit_pct,
        'fixed_stop': fixed_stop,
        'trailing_stop': trailing_stop,
    }


def analyze_portfolio():
    """分析整个组合"""
    config_file = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\config\portfolio_config.json'
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    positions = config['positions']
    
    print(f"\n{'#'*55}")
    print(f"#     📊 股票投资风险管理分析")
    print(f"#     版本: v1.0 | 日期: 2026-04-24")
    print(f"{'#'*55}")
    
    results = []
    for pos in positions:
        r = analyze_position(pos['code'], pos['name'], pos['shares'], pos['avg_cost'])
        if r:
            results.append(r)
    
    # 组合汇总
    total_cost = sum(p['avg_cost'] * p['shares'] for p in positions)
    codes = ['sh' + p['code'] for p in positions]
    quotes = get_realtime_quote(codes)
    total_market = sum(q['price'] * p['shares'] for p, q in zip(positions, (quotes.get('sh'+p['code'], {}) for p in positions)) if 'sh'+p['code'] in quotes)
    
    portfolio_profit = total_market - total_cost
    portfolio_profit_pct = (total_market / total_cost - 1) * 100
    
    print(f"\n{'='*55}")
    print(f"  【组合汇总】")
    print(f"{'='*55}")
    print(f"  💰 总成本: {total_cost:,.0f}元")
    print(f"  📈 总市值: {total_market:,.0f}元")
    print(f"  {'📈' if portfolio_profit >= 0 else '📉'} 盈亏: {portfolio_profit:+,.0f}元 ({portfolio_profit_pct:+.2f}%)")
    
    # 风险等级
    if portfolio_profit < 0:
        risk = abs(portfolio_profit) / total_cost * 100
        if risk > 10:
            risk_level = "🔴 高风险"
        elif risk > 5:
            risk_level = "🟡 中风险"
        else:
            risk_level = "🟢 低风险"
    else:
        risk_level = "🟢 盈利状态"
    
    print(f"  组合风险等级: {risk_level}")
    print(f"{'='*55}")
    
    # 建议
    print(f"\n📋 操作建议:")
    for r in results:
        if r['profit_pct'] < -5:
            print(f"  ⚠️ {r['name']}: 浮亏超过5%，关注是否破止损")
        elif r['profit_pct'] > 10:
            print(f"  💡 {r['name']}: 盈利超过10%，可考虑分批卖出")
        else:
            print(f"  ➡️ {r['name']}: 继续持有观察")


if __name__ == "__main__":
    analyze_portfolio()
