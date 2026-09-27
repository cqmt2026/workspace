"""账户标准格式"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Position:
    """持仓信息"""
    code: str                       # 股票代码
    volume: int = 0                 # 持仓数量
    avg_cost: float = 0.0           # 平均成本
    current_price: float = 0.0      # 当前价格
    market_value: float = 0.0       # 市值
    profit: float = 0.0             # 盈亏
    profit_pct: float = 0.0         # 盈亏比例
    days_held: int = 0              # 持有天数

    def update_market_value(self, price: float):
        """更新市值"""
        self.current_price = price
        self.market_value = self.volume * price
        self.profit = self.market_value - self.volume * self.avg_cost
        if self.avg_cost > 0:
            self.profit_pct = self.profit / (self.volume * self.avg_cost)


@dataclass
class Account:
    """账户信息"""
    date: str                       # 日期 (YYYY-MM-DD)
    total_value: float = 0.0        # 总资产
    cash: float = 0.0               # 现金
    positions: Dict[str, Position] = field(default_factory=dict)  # 持仓 {code: Position}
    frozen_cash: float = 0.0        # 冻结资金
    commission_paid: float = 0.0    # 累计手续费
    tax_paid: float = 0.0           # 累计印花税
    initial_capital: float = 0.0    # 初始资金

    def position_value(self) -> float:
        """持仓市值"""
        return sum(p.market_value for p in self.positions.values())

    def position_count(self) -> int:
        """持仓数量"""
        return len(self.positions)

    def is_empty(self) -> bool:
        """是否空仓"""
        return self.position_count() == 0

    def get_position(self, code: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(code)

    def has_position(self, code: str) -> bool:
        """是否持有某股票"""
        return code in self.positions

    def total_return(self) -> float:
        """总收益率"""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_value - self.initial_capital) / self.initial_capital

    def cash_ratio(self) -> float:
        """现金比例"""
        if self.total_value == 0:
            return 1.0
        return self.cash / self.total_value

    def is_margin_call(self) -> bool:
        """是否触发保证金追缴 (总资产 < 初始资金 * 0.85)"""
        return self.total_value < self.initial_capital * 0.85