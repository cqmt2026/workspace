# -*- coding: utf-8 -*-
"""
净值追踪模块 tracker.py
实时/日终净值计算，持仓盈亏追踪
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# 导入持仓管理
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from portfolio.positions import get_manager


class NetValueTracker:
    """净值追踪器"""

    def __init__(self, config_path: str = None):
        self.position_manager = get_manager(config_path)

    def get_realtime_value(self, price_map: Dict[str, float]) -> Dict:
        """
        计算实时净值

        Args:
            price_map: {symbol: price} 实时价格字典

        Returns:
            净值报告
        """
        positions = self.position_manager.get_all_positions()
        initial_capital = self.position_manager.config.get("portfolio", {}).get("initial_capital", 0)

        position_details = []
        total_cost = 0
        total_value = 0

        for pos in positions:
            sym = pos["code"]
            cost = pos["shares"] * pos["avg_cost"]
            price = price_map.get(sym, pos["avg_cost"])  # 无实时价用成本价
            value = pos["shares"] * price
            profit = value - cost
            profit_rate = profit / cost * 100 if cost > 0 else 0

            position_details.append({
                "symbol": sym,
                "name": pos["name"],
                "quantity": pos["shares"],
                "cost": pos["avg_cost"],
                "current_price": price,
                "cost_total": cost,
                "value": value,
                "profit": profit,
                "profit_rate": profit_rate,
                "position_ratio": value / initial_capital * 100 if initial_capital > 0 else 0
            })

            total_cost += cost
            total_value += value

        cash = initial_capital - total_cost
        total_assets = cash + total_value
        total_profit = total_value - total_cost
        profit_rate = total_profit / total_cost * 100 if total_cost > 0 else 0
        nav = total_assets / initial_capital if initial_capital > 0 else 1.0

        return {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "initial_capital": initial_capital,
            "cash": cash,
            "total_cost": total_cost,
            "total_value": total_value,
            "total_assets": total_assets,
            "total_profit": total_profit,
            "profit_rate": profit_rate,
            "nav": nav,
            "position_count": len([p for p in positions if p.get("quantity", 0) > 0]),
            "positions": position_details
        }

    def get_daily_snapshot(self, price_map: Dict[str, float]) -> str:
        """生成每日持仓快照（Markdown格式）"""
        report = self.get_realtime_value(price_map)

        lines = []
        lines.append(f"# 组合净值快照 · {report['date']}")
        lines.append("")
        lines.append(f"**初始资金**: {report['initial_capital']:,.2f} 元")
        lines.append(f"**现金**: {report['cash']:,.2f} 元")
        lines.append(f"**持仓市值**: {report['total_value']:,.2f} 元")
        lines.append(f"**总资产**: {report['total_assets']:,.2f} 元")
        lines.append(f"**累计收益**: {report['total_profit']:+,.2f} 元 ({report['profit_rate']:+.2f}%)")
        lines.append(f"**净值**: {report['nav']:.4f}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 持仓明细")
        lines.append("")

        if report["positions"]:
            lines.append("| 股票 | 持仓 | 成本 | 现价 | 盈亏 | 收益率 | 仓位 |")
            lines.append("|------|------|------|------|------|--------|------|")
            for p in report["positions"]:
                lines.append(f"| {p['name']} | {p['quantity']} | {p['cost']:.2f} | {p['current_price']:.2f} | {p['profit']:+,.2f} | {p['profit_rate']:+.2f}% | {p['position_ratio']:.1f}% |")
        else:
            lines.append("*暂无持仓*")

        lines.append("")
        lines.append("---")
        lines.append(f"*由 可悦🌸 生成于 {report['date']}*")

        return "\n".join(lines)

    def get_profit_curve(self) -> Dict:
        """
        获取收益曲线数据（从交易记录推算）
        简化版：仅记录每日净值点
        """
        # TODO: 后续对接实际净值历史数据
        return {
            "dates": [],
            "values": [],
            "note": "需对接交易记录历史生成完整收益曲线"
        }


# 便捷函数
_tracker = None

def get_tracker(config_path: str = None) -> NetValueTracker:
    """获取净值追踪器单例"""
    global _tracker
    if _tracker is None:
        _tracker = NetValueTracker(config_path)
    return _tracker


def get_realtime_value(price_map: Dict[str, float]) -> Dict:
    """计算实时净值（便捷函数）"""
    return get_tracker().get_realtime_value(price_map)


# 测试（需配合行情数据）
if __name__ == "__main__":
    tracker = NetValueTracker()

    print("=== 净值追踪测试 ===\n")

    # 模拟实时价格
    price_map = {
        "000591.SZ": 6.62,  # 太阳能
        "000001.SZ": 12.50  # 平安银行
    }

    report = tracker.get_realtime_value(price_map)

    print(f"日期: {report['date']}")
    print(f"初始资金: {report['initial_capital']:,.2f}")
    print(f"现金: {report['cash']:,.2f}")
    print(f"持仓市值: {report['total_value']:,.2f}")
    print(f"总资产: {report['total_assets']:,.2f}")
    print(f"累计收益: {report['total_profit']:+,.2f} ({report['profit_rate']:+.2f}%)")
    print(f"净值: {report['nav']:.4f}")
    print(f"持仓数量: {report['position_count']} 只")
    print()

    if report["positions"]:
        print("持仓明细:")
        for p in report["positions"]:
            print(f"  {p['name']}: {p['quantity']}股, 成本{p['cost']:.2f}, 现价{p['current_price']:.2f}, 盈亏{p['profit']:+,.2f} ({p['profit_rate']:+.2f}%)")
    else:
        print("（零持仓）")
