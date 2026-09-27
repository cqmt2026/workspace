"""信号标准格式"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Signal:
    """交易信号

    策略输出信号，组合管理器根据信号计算具体仓位。
    """
    date: str                       # 信号日期 (YYYY-MM-DD)
    code: str                       # 股票代码 (统一格式: sz.000001)
    direction: str                  # 方向: buy / sell / close
    price: float                    # 信号价格
    volume: float = 0               # 数量 (0表示由组合管理器按资金比例计算)
    weight: float = 1.0             # 仓位权重 (0~1)
    source: str = ''                # 信号来源 (策略名)
    reason: str = ''                # 信号理由
    confidence: float = 0.5         # 置信度 (0~1, 标准化)
    risk_check: Optional[dict] = None  # 风控检查结果

    def __post_init__(self):
        if self.direction not in ('buy', 'sell', 'close'):
            raise ValueError(f"无效的方向: {self.direction}")
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"置信度必须在0~1之间: {self.confidence}")
        if not 0 <= self.weight <= 1:
            raise ValueError(f"权重必须在0~1之间: {self.weight}")