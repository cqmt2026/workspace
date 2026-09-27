# -*- coding: utf-8 -*-
"""
持仓录入接口 position_add.py
快速添加持仓的命令行工具

用法：
    python position_add.py <代码> <名称> <数量> <成本> [日期]
    python position_add.py 000591.SZ 太阳能 10000 6.50 2026-03-01
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from portfolio import add_position


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) < 4:
        print("用法: python position_add.py <代码> <名称> <数量> <成本> [日期]")
        print("示例: python position_add.py 000591.SZ 太阳能 10000 6.50 2026-03-01")
        sys.exit(1)

    symbol = args[0]
    name = args[1]
    quantity = int(args[2])
    cost = float(args[3])
    buy_date = args[4] if len(args) > 4 else None

    result = add_position(symbol, name, quantity, cost, buy_date)

    if result["success"]:
        print(f"[OK] 成功添加持仓: {name} ({symbol})")
        print(f"     数量: {quantity} 股")
        print(f"     成本: {cost:.2f} 元")
        print(f"     日期: {buy_date or '今天'}")
    else:
        print(f"[FAIL] 添加失败: {result['error']}")
