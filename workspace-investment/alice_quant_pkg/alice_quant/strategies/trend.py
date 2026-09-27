"""趋势跟踪策略

均线多头排列 + 量价配合。
"""
from typing import List
from ..core.signal import Signal
from ..core.context import Context
from .base import BaseStrategy


class TrendStrategy(BaseStrategy):
    """趋势跟踪策略

    买入条件:
      1. MA5 > MA10 > MA20 > MA60 (均线多头排列)
      2. 收盘价在MA20上方
      3. 量比 > 1 (量价配合)
      4. RSI > 50 (非超卖区)
    
    卖出条件:
      1. 收盘价跌破MA20
      2. 或 RSI > 80 (超买)
      3. 或 持仓超过20个交易日
    """

    def __init__(self, name: str = 'trend', params: dict = None,
                 feature_engine=None, logger=None):
        params = params or {
            'rsi_buy_min': 50,
            'rsi_sell_max': 80,
            'vol_ratio_min': 1.0,
            'max_hold_days': 20,
        }
        super().__init__(name, params, feature_engine, logger)

    def on_start(self, context: Context):
        self.watch_codes = context.watch_codes or []
        if self.watch_codes:
            self.prefetch_factors(
                codes=self.watch_codes,
                factor_names=['ma_5', 'ma_10', 'ma_20', 'ma_60',
                             'rsi_14', 'vol_ratio'],
                dates=context.all_dates
            )

    def on_bar(self, data, context: Context) -> List[Signal]:
        date = context.current_date
        signals = []
        account = context.account

        # 检查现有持仓是否需要卖出
        if account:
            for code, pos in account.positions.items():
                if pos.days_held >= self.params['max_hold_days']:
                    signals.append(Signal(
                        date=date, code=code, direction='sell',
                        price=pos.current_price, volume=pos.volume,
                        source=self.name, reason='持有超时',
                        confidence=0.9
                    ))
                    continue

                ma20 = self.get_cached_factor(code, 'ma_20', date)
                rsi = self.get_cached_factor(code, 'rsi_14', date)
                if ma20 and pos.current_price < ma20:
                    signals.append(Signal(
                        date=date, code=code, direction='sell',
                        price=pos.current_price, volume=pos.volume,
                        source=self.name, reason='跌破MA20',
                        confidence=0.9
                    ))
                elif rsi and rsi > self.params['rsi_sell_max']:
                    signals.append(Signal(
                        date=date, code=code, direction='sell',
                        price=pos.current_price, volume=pos.volume,
                        source=self.name, reason='RSI超买',
                        confidence=0.8
                    ))

        # 检查买入机会
        for code in self.watch_codes:
            if account and account.has_position(code):
                continue

            ma5 = self.get_cached_factor(code, 'ma_5', date)
            ma10 = self.get_cached_factor(code, 'ma_10', date)
            ma20 = self.get_cached_factor(code, 'ma_20', date)
            ma60 = self.get_cached_factor(code, 'ma_60', date)
            rsi = self.get_cached_factor(code, 'rsi_14', date)
            vol_ratio = self.get_cached_factor(code, 'vol_ratio', date)

            if any(v is None for v in [ma5, ma10, ma20, ma60, rsi, vol_ratio]):
                continue

            buy = True
            reasons = []

            # 均线多头排列
            if ma5 > ma10 > ma20 > ma60:
                reasons.append("均线多头")
            else:
                buy = False

            # RSI > 50
            if rsi >= self.params['rsi_buy_min']:
                reasons.append(f"RSI={rsi:.0f}")
            else:
                buy = False

            # 量比 > 1
            if vol_ratio >= self.params['vol_ratio_min']:
                reasons.append(f"量比={vol_ratio:.1f}")
            else:
                buy = False

            if buy:
                confidence = 0.7 + (rsi / 100) * 0.2  # RSI越高置信度越高
                signals.append(Signal(
                    date=date, code=code, direction='buy',
                    price=data.get('close', 0), volume=0,
                    weight=1.0, source=self.name,
                    reason='; '.join(reasons),
                    confidence=min(confidence, 0.95)
                ))

        return signals