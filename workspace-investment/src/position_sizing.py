# -*- coding: utf-8 -*-
"""
仓位管理模块 v1.0
第一阶段核心内容：教主人如何科学计算仓位
"""

import json

# ============ 风险管理核心参数 ============
RISK_PARAMS = {
    "max_risk_per_trade": 0.02,       # 单笔最大风险敞口 2%
    "max_portfolio_risk": 0.15,       # 组合最大风险 15%
    "stop_loss_pct": 0.05,            # 止损幅度 5%
    "reward_risk_ratio": 2.0,        # 盈亏比 1:2
}

def calculate_position_size(account_size, price, stop_loss_pct=None):
    """
    计算仓位：亏损时买多少股
    
    公式：仓位 = 账户金额 × 风险比例 / 每股风险
    
    参数：
    - account_size: 账户总金额
    - price: 买入价格
    - stop_loss_pct: 止损比例（默认5%）
    
    示例：
    - 账户10万，风险2%
    - 买入价10元，止损9.5元（-5%）
    - 每股风险 = 0.5元
    - 仓位 = 2000 / 0.5 = 4000股 = 4万元
    """
    if stop_loss_pct is None:
        stop_loss_pct = RISK_PARAMS["stop_loss_pct"]
    
    risk_amount = account_size * RISK_PARAMS["max_risk_per_trade"]  # 本次允许亏损金额
    risk_per_share = price * stop_loss_pct  # 每股承担的亏损
    
    shares = int(risk_amount / risk_per_share)  # 可买入股数
    cost = shares * price  # 需要投入的资金
    
    return {
        "risk_amount": risk_amount,           # 本次允许亏损
        "risk_per_share": risk_per_share,     # 每股风险
        "shares": shares,                      # 可买入股数
        "cost": cost,                          # 需要资金
        "cost_pct": cost / account_size * 100,  # 仓位占比
        "stop_loss_price": price * (1 - stop_loss_pct),  # 止损价
    }


def calculate_portfolio_risk(positions, prices):
    """
    计算组合风险敞口
    
    返回：
    - 各持仓的风险敞口
    - 组合总风险
    """
    total_risk = 0
    results = []
    
    for pos in positions:
        code = pos['code']
        shares = pos['shares']
        cost = pos['avg_cost']
        
        # 从实时价格获取当前价
        current_price = prices.get(code, cost)
        
        # 计算浮亏/浮盈
        profit = (current_price - cost) * shares
        profit_pct = (current_price / cost - 1) * 100
        
        # 如果浮亏，计算风险敞口
        if profit < 0:
            risk_exposure = abs(profit)
        else:
            risk_exposure = 0  # 盈利持仓不计入风险
        
        total_risk += risk_exposure
        
        results.append({
            "code": code,
            "name": pos['name'],
            "shares": shares,
            "cost": cost,
            "current_price": current_price,
            "profit": profit,
            "profit_pct": profit_pct,
            "risk_exposure": risk_exposure,
        })
    
    return results, total_risk


def print_position_report(account_size=100000):
    """打印仓位管理报告"""
    
    print("="*60)
    print("📊 仓位管理计算器 v1.0")
    print("="*60)
    
    print(f"\n💰 账户规模: {account_size:,}元")
    print(f"📋 风险管理参数:")
    print(f"   单笔最大风险敞口: {RISK_PARAMS['max_risk_per_trade']*100:.0f}%")
    print(f"   组合最大风险敞口: {RISK_PARAMS['max_portfolio_risk']*100:.0f}%")
    print(f"   止损幅度: {RISK_PARAMS['stop_loss_pct']*100:.0f}%")
    print(f"   盈亏比目标: 1:{RISK_PARAMS['reward_risk_ratio']:.0f}")
    
    print(f"\n{'='*60}")
    print("📈 仓位计算示例")
    print("="*60)
    
    # 示例：10万账户，不同价格买入
    examples = [
        (10.00, "10元股票"),
        (50.00, "50元股票"),
        (100.00, "100元股票"),
    ]
    
    for price, desc in examples:
        result = calculate_position_size(account_size, price)
        
        print(f"\n{desc} (买入价: {price:.2f}元)")
        print(f"  本次允许亏损: {result['risk_amount']:,.0f}元")
        print(f"  每股风险: {result['risk_per_share']:.2f}元")
        print(f"  可买入股数: {result['shares']}股")
        print(f"  需要资金: {result['cost']:,.0f}元 (占总账户 {result['cost_pct']:.1f}%)")
        print(f"  止损价: {result['stop_loss_price']:.2f}元")
    
    print(f"\n{'='*60}")
    print("💡 核心原则")
    print("="*60)
    print("""
  1. 【单笔风险控制】
     每笔交易只允许亏损账户的2%
     例：10万账户，每笔最多亏2000元
  
  2. 【止损幅度固定】
     止损幅度5%，不变
     根据止损幅度反推可买入股数
  
  3. 【盈亏比1:2】
     如果止损1000元，盈利目标2000元
     成功率仅需34%就能盈利
  
  4. 【分散持仓】
     组合同时持有2-4只股票
     单只股票仓位不超过25%
    """)


def analyze_existing_position(code, name, shares, cost, current_price):
    """分析现有持仓的仓位是否合理"""
    
    print(f"\n{'='*60}")
    print(f"📋 持仓分析: {name} ({code})")
    print(f"{'='*60}")
    
    # 基础计算
    market_value = shares * current_price
    cost_total = shares * cost
    profit = market_value - cost_total
    profit_pct = (current_price / cost - 1) * 100
    
    # 止损价位
    stop_loss_price = cost * (1 - RISK_PARAMS['stop_loss_pct'])
    max_loss = (cost - stop_loss_price) * shares
    
    print(f"\n  基本信息:")
    print(f"    持股: {shares}股")
    print(f"    成本: {cost:.2f}元")
    print(f"    现价: {current_price:.2f}元")
    print(f"    止损: {stop_loss_price:.2f}元 (-5%)")
    
    print(f"\n  盈亏情况:")
    print(f"    市值: {market_value:,.0f}元")
    print(f"    成本: {cost_total:,.0f}元")
    print(f"    盈亏: {profit:+,.0f}元 ({profit_pct:+.2f}%)")
    
    print(f"\n  风险评估:")
    print(f"    若触发止损，最大亏损: {max_loss:,.0f}元")
    
    # 评估仓位是否合理
    if abs(profit_pct) > 10:
        print(f"\n  ⚠️ 持仓盈亏较大，需密切关注")
    
    if profit > 0:
        # 盈利持仓，可以考虑移动止损
        trailing_stop = current_price * (1 - 0.03)
        print(f"\n  ✅ 盈利持仓，可设置移动止损: {trailing_stop:.2f}元")
    else:
        # 亏损持仓
        loss_ratio = abs(profit) / max_loss * 100 if max_loss > 0 else 0
        print(f"\n  ⚠️ 浮亏持仓，已消耗止损空间: {loss_ratio:.0f}%")
        if loss_ratio > 80:
            print(f"  🚨 警告：接近止损线！")


if __name__ == "__main__":
    print_position_report(account_size=100000)
