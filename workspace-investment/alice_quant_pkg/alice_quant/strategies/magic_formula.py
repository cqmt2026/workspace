"""神奇公式策略 - Joel Greenblatt经典策略

ROIC + Earnings Yield 双因子排名选股。
"""
from typing import List
from ..core.signal import Signal
from ..core.context import Context
from .base import BaseStrategy


class MagicFormulaStrategy(BaseStrategy):
    """神奇公式策略

    选股条件:
      1. ROIC > 5%
      2. PE_TTM 在 5~30 之间
      3. 市值 > 50亿
      4. 排除ST股和金融股
    
    排名方法:
      ROIC排名 + 1/PE_TTM排名 (Earnings Yield替代)
      综合分越低越优
    """

    def __init__(self, name: str = 'magic_formula', params: dict = None,
                 feature_engine=None, logger=None):
        params = params or {
            'min_roic': 5.0,
            'min_pe': 5,
            'max_pe': 30,
            'min_market_cap': 50,  # 亿
            'top_n': 20,           # 选前N只
            'rebalance_months': 3,  # 每3个月再平衡
        }
        super().__init__(name, params, feature_engine, logger)

    def on_start(self, context: Context):
        self.watch_codes = context.watch_codes or []
        self._last_rebalance = ''

    def on_bar(self, data, context: Context) -> List[Signal]:
        date = context.current_date
        signals = []

        # 检查是否需要再平衡
        if self._should_rebalance(date):
            self._last_rebalance = date
            # TODO: 从DataHub获取财务数据，计算排名
            # 简化版：发出再平衡信号
            signals.append(Signal(
                date=date, code='REBALANCE', direction='close',
                price=0, volume=0,
                source=self.name, reason='月度再平衡',
                confidence=1.0
            ))

        return signals

    def _should_rebalance(self, date: str) -> bool:
        """检查是否需要再平衡"""
        if not self._last_rebalance:
            return True
        from datetime import datetime
        d1 = datetime.strptime(date, '%Y-%m-%d')
        d2 = datetime.strptime(self._last_rebalance, '%Y-%m-%d')
        months = (d1.year - d2.year) * 12 + (d1.month - d2.month)
        return months >= self.params['rebalance_months']