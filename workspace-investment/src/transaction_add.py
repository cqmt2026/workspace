# -*- coding: utf-8 -*-
"""
交易记录录入接口 transaction_add.py
记录买入/卖出的命令行工具

用法：
    python transaction_add.py buy <代码> <名称> <数量> <价格> [日期]
    python transaction_add.py sell 000591.SZ 太阳能 5000 7.20 2026-04-15
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from portfolio import add_transaction


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) < 5:
        print("用法: python transaction_add.py <方向> <代码> <名称> <数量> <价格> [日期]")
        print("示例(买入): python transaction_add.py buy 000591.SZ 太阳能 10000 6.50 2026-03-01")
        print("示例(卖出): python transaction_add.py sell 000591.SZ 太阳能 5000 7.20 2026-04-15")
        sys.exit(1)

    direction = args[0]
    if direction not in ("buy", "sell"):
        print("[FAIL] 方向必须是 buy 或 sell")
        sys.exit(1)

    symbol = args[1]
    name = args[2]
    quantity = int(args[3])
    price = float(args[4])
    date = args[5] if len(args) > 5 else None

    result = add_transaction(symbol, name, direction, quantity, price, date)

    print(f"[OK] 交易已记录")
    print(f"     {direction.upper()}: {name} ({symbol})")
    print(f"     数量: {quantity} 股 @ {price:.2f}")
    print(f"     总额: {quantity * price:.2f} 元")
    print(f"     日期: {date or '今天'}")
