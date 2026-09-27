# -*- coding: utf-8 -*-
"""
一键净值报告脚本 portfolio_report.py
自动获取行情 + 计算净值 + 生成报告

运行方式：
    python portfolio_report.py
"""

import sys
import os
from datetime import datetime

# 添加 src/ 目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from portfolio.price_loader import get_price_map
from portfolio.tracker import get_tracker
from portfolio.daily_report import generate_daily_report
from portfolio.weekly_report import generate_weekly_report


def generate_portfolio_report() -> dict:
    """
    生成完整组合报告

    Returns:
        报告结果字典
    """
    print("=" * 50)
    print("组合净值报告生成")
    print("=" * 50)
    print()

    # 1. 获取持仓列表
    tracker = get_tracker()
    positions = tracker.position_manager.get_all_positions()
    print(f"持仓数量: {len(positions)} 只")

    if not positions:
        print("[WARN] 零持仓，跳过行情获取")
        return {"status": "empty", "message": "零持仓"}

    # 2. 获取实时行情
    # 构造完整代码：market + code（如 sh600549, sz000539）
    symbols = [(pos['market'] + pos['code']) for pos in positions]
    print(f"获取行情: {symbols}")
    price_map = get_price_map(symbols)
    print(f"成功获取: {len(price_map)} 只")
    print()

    # 同时建立纯代码的映射（供tracker使用）
    code_to_price = {}
    for pos in positions:
        full_sym = pos['market'] + pos['code']
        if full_sym in price_map:
            code_to_price[pos['code']] = price_map[full_sym]

    for sym, price in price_map.items():
        print(f"  {sym}: {price:.2f}")

    print()

    # 3. 计算净值（传入纯代码价格映射）
    print("计算净值...")
    report = tracker.get_realtime_value(code_to_price)
    print(f"  总资产: {report['total_assets']:,.2f}")
    print(f"  累计收益: {report['total_profit']:+,.2f} ({report['profit_rate']:+.2f}%)")
    print(f"  净值: {report['nav']:.4f}")
    print()

    # 4. 生成日报
    print("生成日报...")
    daily_path = generate_daily_report(price_map)
    print(f"  {daily_path}")

    # 5. 生成周报
    print("生成周报...")
    weekly_path = generate_weekly_report(price_map)
    print(f"  {weekly_path}")

    print()
    print("=" * 50)
    print("[OK] 报告生成完成")
    print("=" * 50)

    return {
        "status": "success",
        "report": report,
        "daily_report": daily_path,
        "weekly_report": weekly_path
    }


# 命令行入口
if __name__ == "__main__":
    result = generate_portfolio_report()
    if result["status"] == "success":
        print()
        print("报告摘要:")
        print(f"  总资产: {result['report']['total_assets']:,.2f}")
        print(f"  净值: {result['report']['nav']:.4f}")
