"""滑点模型 - 固定/比例/VWAP偏离"""
import numpy as np


class SlippageModel:
    """滑点模型"""

    def __init__(self, config=None):
        self._config = config
        self._model = self._get_config('backtest.slippage.model', 'fixed')
        self._fixed_slippage = self._get_config('backtest.slippage.fixed', 0.001)
        self._ratio_slippage = self._get_config('backtest.slippage.ratio', 0.001)
        self._tail_slippage = self._get_config('backtest.tail_slippage', 0.001)

    def apply(self, price: float, direction: str) -> float:
        """应用滑点

        Args:
            price: 原始价格
            direction: 方向 (buy/sell)

        Returns:
            含滑点的价格
        """
        if direction == 'buy':
            return price * (1 + self._fixed_slippage)
        else:
            return price * (1 - self._fixed_slippage)

    def apply_tail(self, price: float) -> float:
        """尾盘滑点（模拟14:50买入）"""
        return price * (1 + self._tail_slippage)

    def _get_config(self, key: str, default):
        if self._config:
            return self._config.get(key, default)
        return default