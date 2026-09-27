"""滑点模型 - 固定/比例/VWAP偏离

支持：
- fixed: 固定比例滑点（默认0.1%）
- ratio: 按成交量比例滑点
- tail: 尾盘模拟滑点（14:50买入，略高于收盘价）
"""
import numpy as np


class SlippageModel:
    """滑点模型"""

    def __init__(self, config=None):
        self._config = config
        self._model = self._get_config('backtest.slippage.model', 'fixed')
        self._fixed_slippage = self._get_config('backtest.slippage.fixed', 0.001)
        self._ratio_slippage = self._get_config('backtest.slippage.ratio', 0.001)
        self._tail_slippage = self._get_config('backtest.slippage.tail', 0.002)

    def apply(self, price: float, direction: str) -> float:
        """应用滑点

        根据配置的模型类型计算含滑点价格。

        Args:
            price: 原始价格
            direction: 方向 (buy/sell)

        Returns:
            含滑点的价格
        """
        if self._model == 'fixed':
            return self._apply_fixed(price, direction)
        elif self._model == 'ratio':
            return self._apply_ratio(price, direction)
        elif self._model == 'tail':
            return self._apply_tail(price, direction)
        return self._apply_fixed(price, direction)

    def apply_tail(self, price: float, direction: str = 'buy') -> float:
        """尾盘滑点（模拟14:50买入/卖出）

        尾盘流动性下降，滑点略高于常规。
        """
        if direction == 'buy':
            return price * (1 + self._tail_slippage)
        else:
            return price * (1 - self._tail_slippage)

    def _apply_fixed(self, price: float, direction: str) -> float:
        """固定比例滑点"""
        if direction == 'buy':
            return price * (1 + self._fixed_slippage)
        else:
            return price * (1 - self._fixed_slippage)

    def _apply_ratio(self, price: float, direction: str) -> float:
        """按成交量比例滑点（简化版）"""
        # 完整版需要成交量数据计算冲击成本
        if direction == 'buy':
            return price * (1 + self._ratio_slippage)
        else:
            return price * (1 - self._ratio_slippage)

    def _get_config(self, key: str, default):
        if self._config:
            return self._config.get(key, default)
        return default