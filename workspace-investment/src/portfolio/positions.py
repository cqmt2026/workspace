# -*- coding: utf-8 -*-
"""
持仓管理模块 positions.py
管理股票持仓：录入、查询、更新
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class PositionManager:
    """持仓管理器"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config", "portfolio_config.json"
            )
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"positions": [], "portfolio": {"initial_capital": 0}}

    def _save_config(self):
        """保存配置文件"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def add_position(self, symbol: str, name: str, quantity: int,
                     cost: float, buy_date: str = None, source: str = "manual",
                     notes: str = "") -> Dict:
        """
        添加持仓

        Args:
            symbol: 股票代码（如 000001.SZ）
            name: 股票名称
            quantity: 持仓数量
            cost: 成本价
            buy_date: 买入日期（YYYY-MM-DD）
            source: 来源（manual/eastmoney/import）
            notes: 备注

        Returns:
            添加结果
        """
        if buy_date is None:
            buy_date = datetime.now().strftime("%Y-%m-%d")

        # 检查是否已存在
        for pos in self.config.get("positions", []):
            if pos["symbol"] == symbol:
                return {"success": False, "error": f"{symbol} 已存在，请使用 update_position"}

        position = {
            "symbol": symbol,
            "name": name,
            "quantity": quantity,
            "cost": cost,
            "buy_date": buy_date,
            "source": source,
            "notes": notes,
            "added_at": datetime.now().isoformat()
        }

        self.config.setdefault("positions", []).append(position)
        self._save_config()

        return {"success": True, "position": position}

    def update_position(self, symbol: str, quantity: int = None,
                        cost: float = None, notes: str = None) -> Dict:
        """
        更新持仓

        Args:
            symbol: 股票代码
            quantity: 新持仓数量（None则不变）
            cost: 新成本价（None则不变）
            notes: 新备注（None则不变）

        Returns:
            更新结果
        """
        for pos in self.config.get("positions", []):
            if pos["symbol"] == symbol:
                if quantity is not None:
                    pos["quantity"] = quantity
                if cost is not None:
                    pos["cost"] = cost
                if notes is not None:
                    pos["notes"] = notes
                pos["updated_at"] = datetime.now().isoformat()
                self._save_config()
                return {"success": True, "position": pos}

        return {"success": False, "error": f"{symbol} 不存在"}

    def remove_position(self, symbol: str) -> Dict:
        """移除持仓"""
        positions = self.config.get("positions", [])
        for i, pos in enumerate(positions):
            if pos["symbol"] == symbol:
                removed = positions.pop(i)
                self._save_config()
                return {"success": True, "removed": removed}
        return {"success": False, "error": f"{symbol} 不存在"}

    def get_position(self, symbol: str) -> Optional[Dict]:
        """获取单个持仓"""
        for pos in self.config.get("positions", []):
            if pos["symbol"] == symbol:
                return pos
        return None

    def get_all_positions(self) -> List[Dict]:
        """获取所有持仓"""
        return self.config.get("positions", [])

    def get_total_cost(self) -> float:
        """计算总持仓成本"""
        total = 0
        for pos in self.config.get("positions", []):
            total += pos["quantity"] * pos["cost"]
        return total

    def get_position_count(self) -> int:
        """获取持仓数量"""
        return len([p for p in self.config.get("positions", [])
                     if p.get("quantity", 0) > 0])


# 便捷函数
_manager = None

def get_manager(config_path: str = None) -> PositionManager:
    """获取持仓管理器单例"""
    global _manager
    if _manager is None:
        _manager = PositionManager(config_path)
    return _manager


def add_position(symbol: str, name: str, quantity: int, cost: float,
                 buy_date: str = None, source: str = "manual", notes: str = "") -> Dict:
    """添加持仓（便捷函数）"""
    return get_manager().add_position(symbol, name, quantity, cost, buy_date, source, notes)


def update_position(symbol: str, quantity: int = None,
                    cost: float = None, notes: str = None) -> Dict:
    """更新持仓（便捷函数）"""
    return get_manager().update_position(symbol, quantity, cost, notes)


def get_all_positions() -> List[Dict]:
    """获取所有持仓（便捷函数）"""
    return get_manager().get_all_positions()


# 测试
if __name__ == "__main__":
    manager = PositionManager()

    print("=== 持仓管理测试 ===\n")

    # 添加测试持仓
    print("1. 添加持仓测试")
    result = manager.add_position(
        symbol="000001.SZ",
        name="平安银行",
        quantity=1000,
        cost=12.50,
        buy_date="2026-01-15",
        notes="测试持仓"
    )
    print(f"   结果: {result}\n")

    # 查询所有持仓
    print("2. 所有持仓:")
    for pos in manager.get_all_positions():
        print(f"   {pos['symbol']} {pos['name']}: {pos['quantity']}股，成本{pos['cost']}")

    print(f"\n3. 总持仓成本: {manager.get_total_cost():.2f}元")
    print(f"   持仓数量: {manager.get_position_count()}只")
