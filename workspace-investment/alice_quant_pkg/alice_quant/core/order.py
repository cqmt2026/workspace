"""订单标准格式"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Order:
    """交易订单

    信号处理器将Signal转为Order，回测引擎/执行器处理Order。
    """
    order_id: str                   # 订单ID
    date: str                       # 订单日期 (YYYY-MM-DD)
    code: str                       # 股票代码
    direction: str                  # 方向: buy / sell
    price: float                    # 委托价格
    volume: int                     # 委托数量 (股)
    status: str = 'pending'         # 状态: pending / filled / partial / cancelled
    filled_price: float = 0.0       # 成交均价
    filled_volume: int = 0          # 成交数量
    commission: float = 0.0         # 手续费
    tax: float = 0.0                # 印花税
    slippage: float = 0.0           # 滑点
    source: str = ''                # 信号来源
    reason: str = ''                # 交易理由
    risk_check: Optional[dict] = None  # 风控检查结果

    def is_filled(self) -> bool:
        """是否完全成交"""
        return self.status == 'filled'

    def is_pending(self) -> bool:
        """是否待成交"""
        return self.status == 'pending'

    def fill_value(self) -> float:
        """成交金额"""
        return self.filled_price * self.filled_volume