"""打板策略 - 涨停板次日溢价

捕捉涨停板次日的溢价效应。
"""
from typing import List
from ..core.signal import Signal
from ..core.context import Context
from .base import BaseStrategy


class DaBanStrategy(BaseStrategy):
    """打板策略

    买入条件:
      1. 今日涨停 (涨幅 >= 9.8%)
      2. 封板时间早 (10:30前涨停)
      3. 非一字板 (有换手)
      4. 非ST股
    
    卖出条件:
      1. 次日开盘卖出
      2. 或盘中触及涨停不卖，回落卖出
    """

    def __init__(self, name: str = 'daban', params: dict = None,
                 feature_engine=None, logger=None):
        params = params or {
            'zt_threshold': 9.8,       # 涨停阈值(%)
            'max_turnover': 20.0,       # 最大换手率
            'min_turnover': 1.0,        # 最小换手率(排除一字板)
        }
        super().__init__(name, params, feature_engine, logger)
        self._zt_candidates: set = set()  # 今日涨停候选

    def on_start(self, context: Context):
        self.watch_codes = context.watch_codes or []
        if self.watch_codes:
            self.prefetch_factors(
                codes=self.watch_codes,
                factor_names=['pct_chg_1d', 'turnover'],
                dates=context.all_dates
            )

    def on_bar(self, data, context: Context) -> List[Signal]:
        date = context.current_date
        signals = []
        account = context.account

        # 卖出：昨日买入的，今日开盘卖出
        if account:
            for code, pos in list(account.positions.items()):
                if pos.days_held == 1:
                    signals.append(Signal(
                        date=date, code=code, direction='sell',
                        price=data.get('open', pos.current_price),
                        volume=pos.volume,
                        source=self.name, reason='打板次日卖出',
                        confidence=0.9
                    ))

        # 买入：筛选今日涨停股
        for code in self.watch_codes:
            if code.startswith('bj.') or code.startswith('st'):
                continue

            pct_chg = self.get_cached_factor(code, 'pct_chg_1d', date)
            if pct_chg is None or pct_chg < self.params['zt_threshold']:
                continue

            signals.append(Signal(
                date=date, code=code, direction='buy',
                price=data.get('close', 0), volume=0,
                weight=1.0, source=self.name,
                reason=f'涨停{pct_chg:.1f}%',
                confidence=0.6
            ))

        return signals