# -*- coding: utf-8 -*-
"""
交易记录模块 transactions.py
记录买入/卖出交易历史
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class TransactionManager:
    """交易记录管理器"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data"
            )
        self.data_dir = data_dir
        self.transactions_file = os.path.join(data_dir, "transactions.json")
        self.transactions = self._load_transactions()

    def _load_transactions(self) -> List[Dict]:
        """加载交易记录"""
        if os.path.exists(self.transactions_file):
            try:
                with open(self.transactions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def _save_transactions(self):
        """保存交易记录"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.transactions_file, 'w', encoding='utf-8') as f:
            json.dump(self.transactions, f, ensure_ascii=False, indent=2)

    def add_transaction(self, symbol: str, name: str, direction: str,
                        quantity: int, price: float, date: str = None,
                        commission: float = 0, stamp_tax: float = 0) -> Dict:
        """
        添加交易记录

        Args:
            symbol: 股票代码
            name: 股票名称
            direction: 方向（buy/sell）
            quantity: 数量
            price: 价格
            date: 交易日期（YYYY-MM-DD）
            commission: 佣金
            stamp_tax: 印花税（卖出时收取）

        Returns:
            交易记录
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # 计算费用
        amount = quantity * price
        if commission == 0:
            commission = max(amount * 0.0003, 5)  # 默认佣金万三，最低5元
        if direction == "sell" and stamp_tax == 0:
            stamp_tax = amount * 0.001  # 印花税千一

        transaction = {
            "id": len(self.transactions) + 1,
            "symbol": symbol,
            "name": name,
            "direction": direction,
            "quantity": quantity,
            "price": price,
            "amount": amount,
            "commission": commission,
            "stamp_tax": stamp_tax,
            "total_cost": amount + commission + stamp_tax if direction == "buy" else amount - commission - stamp_tax,
            "date": date,
            "created_at": datetime.now().isoformat()
        }

        self.transactions.append(transaction)
        self._save_transactions()

        return transaction

    def get_transactions(self, symbol: str = None, direction: str = None,
                         start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        查询交易记录

        Args:
            symbol: 股票代码过滤
            direction: 方向过滤（buy/sell）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            交易记录列表
        """
        result = self.transactions

        if symbol:
            result = [t for t in result if t["symbol"] == symbol]
        if direction:
            result = [t for t in result if t["direction"] == direction]
        if start_date:
            result = [t for t in result if t["date"] >= start_date]
        if end_date:
            result = [t for t in result if t["date"] <= end_date]

        return result

    def get_profit_summary(self, symbol: str = None) -> Dict:
        """
        获取盈亏汇总

        Args:
            symbol: 股票代码（None则全部）

        Returns:
            盈亏汇总
        """
        transactions = self.get_transactions(symbol=symbol)

        total_buy = sum(t["total_cost"] for t in transactions if t["direction"] == "buy")
        total_sell = sum(t["total_cost"] for t in transactions if t["direction"] == "sell")
        buy_count = sum(1 for t in transactions if t["direction"] == "buy")
        sell_count = sum(1 for t in transactions if t["direction"] == "sell")
        total_commission = sum(t["commission"] + t["stamp_tax"] for t in transactions)

        return {
            "symbol": symbol or "全部",
            "buy_count": buy_count,
            "sell_count": sell_count,
            "total_buy_cost": total_buy,
            "total_sell_proceeds": total_sell,
            "net_profit": total_sell - total_buy,
            "profit_rate": (total_sell - total_buy) / total_buy * 100 if total_buy > 0 else 0,
            "total_commission": total_commission
        }

    def get_holding_summary(self) -> Dict:
        """
        获取持仓汇总（根据交易记录推算）

        Returns:
            持仓汇总
        """
        holdings = {}

        for t in self.transactions:
            sym = t["symbol"]
            if sym not in holdings:
                holdings[sym] = {
                    "symbol": sym,
                    "name": t["name"],
                    "quantity": 0,
                    "total_cost": 0
                }

            if t["direction"] == "buy":
                holdings[sym]["quantity"] += t["quantity"]
                holdings[sym]["total_cost"] += t["total_cost"]
            else:  # sell
                holdings[sym]["quantity"] -= t["quantity"]
                # 简化处理：按比例减少成本
                if holdings[sym]["quantity"] > 0:
                    holdings[sym]["total_cost"] -= t["total_cost"] * (t["quantity"] / (holdings[sym]["quantity"] + t["quantity"]))

        # 只返回有持仓的
        return {sym: h for sym, h in holdings.items() if h["quantity"] > 0}


# 便捷函数
_manager = None

def get_manager(data_dir: str = None) -> TransactionManager:
    """获取交易记录管理器单例"""
    global _manager
    if _manager is None:
        _manager = TransactionManager(data_dir)
    return _manager


def add_transaction(symbol: str, name: str, direction: str,
                    quantity: int, price: float, date: str = None,
                    commission: float = 0, stamp_tax: float = 0) -> Dict:
    """添加交易记录（便捷函数）"""
    return get_manager().add_transaction(symbol, name, direction, quantity, price, date, commission, stamp_tax)


def get_transactions(symbol: str = None, direction: str = None) -> List[Dict]:
    """查询交易记录（便捷函数）"""
    return get_manager().get_transactions(symbol, direction)


# 测试
if __name__ == "__main__":
    manager = TransactionManager()

    print("=== 交易记录测试 ===\n")

    # 添加买入记录
    print("1. 添加买入测试")
    t1 = manager.add_transaction(
        symbol="000001.SZ",
        name="平安银行",
        direction="buy",
        quantity=1000,
        price=12.50,
        date="2026-01-15"
    )
    print(f"   买入: {t1['symbol']} {t1['quantity']}股 @{t1['price']}")
    print(f"   总额: {t1['amount']:.2f}，费用: {t1['commission']:.2f}\n")

    # 添加卖出记录
    print("2. 添加卖出测试")
    t2 = manager.add_transaction(
        symbol="000001.SZ",
        name="平安银行",
        direction="sell",
        quantity=500,
        price=13.80,
        date="2026-03-20"
    )
    print(f"   卖出: {t2['symbol']} {t2['quantity']}股 @{t2['price']}")
    print(f"   总额: {t2['amount']:.2f}，佣金: {t2['commission']:.2f}，印花税: {t2['stamp_tax']:.2f}\n")

    # 盈亏汇总
    print("3. 盈亏汇总:")
    summary = manager.get_profit_summary()
    print(f"   买入次数: {summary['buy_count']}")
    print(f"   卖出次数: {summary['sell_count']}")
    print(f"   买入总额: {summary['total_buy_cost']:.2f}")
    print(f"   卖出总额: {summary['total_sell_proceeds']:.2f}")
    print(f"   净收益: {summary['net_profit']:.2f} ({summary['profit_rate']:.2f}%)")
    print(f"   总费用: {summary['total_commission']:.2f}\n")

    # 持仓汇总
    print("4. 持仓汇总:")
    holdings = manager.get_holding_summary()
    for sym, h in holdings.items():
        avg_cost = h["total_cost"] / h["quantity"] if h["quantity"] > 0 else 0
        print(f"   {sym} {h['name']}: {h['quantity']}股，成本 {avg_cost:.2f}")
