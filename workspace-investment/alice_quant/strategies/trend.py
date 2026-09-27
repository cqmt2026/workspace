"""趋势跟踪策略 - 通过FeatureEngine获取因子

买入条件:
  1. MA5 > MA10 > MA20 > MA60 (均线多头排列)
  2. 收盘价在MA20上方
  3. 量比 > 1
  4. RSI > 50

卖出条件:
  1. 收盘价跌破MA20
  2. 或 RSI > 80
  3. 或 持仓超过20个交易日
"""
from typing import List
from ..core.signal import Signal
from ..core.context import Context
from .base import BaseStrategy


class TrendStrategy(BaseStrategy):
    """趋势跟踪策略"""

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
        if self.logger:
            self.logger.info(f"趋势策略启动", codes=len(self.watch_codes))

    def on_bar(self, data, context: Context) -> List[Signal]:
        date = context.current_date
        signals = []
        account = context.account

        for code, bar in data.items():
            close = bar.get('close', 0)
            if close <= 0:
                continue

            # 通过FeatureEngine获取因子
            ma5 = self._get_factor(code, 'ma_5', date)
            ma10 = self._get_factor(code, 'ma_10', date)
            ma20 = self._get_factor(code, 'ma_20', date)
            ma60 = self._get_factor(code, 'ma_60', date)
            rsi = self._get_factor(code, 'rsi_14', date)
            vol_ratio = self._get_factor(code, 'vol_ratio', date)

            if any(v is None for v in [ma5, ma10, ma20, ma60, rsi, vol_ratio]):
                continue

            # 检查现有持仓是否需要卖出
            if account and account.has_position(code):
                pos = account.get_position(code)
                if pos.days_held >= self.params['max_hold_days']:
                    signals.append(Signal(
                        date=date, code=code, direction='sell',
                        price=pos.current_price, volume=pos.volume,
                        source=self.name, reason='持有超时', confidence=0.9
                    ))
                    continue

                if close < ma20:
                    signals.append(Signal(
                        date=date, code=code, direction='sell',
                        price=pos.current_price, volume=pos.volume,
                        source=self.name, reason='跌破MA20', confidence=0.9
                    ))
                elif rsi > self.params['rsi_sell_max']:
                    signals.append(Signal(
                        date=date, code=code, direction='sell',
                        price=pos.current_price, volume=pos.volume,
                        source=self.name, reason='RSI超买', confidence=0.8
                    ))
                continue

            # 买入条件检查
            buy = True
            reasons = []

            if ma5 > ma10 > ma20 > ma60:
                reasons.append("均线多头")
            else:
                buy = False

            if close > ma20:
                reasons.append("站上MA20")
            else:
                buy = False

            if rsi >= self.params['rsi_buy_min']:
                reasons.append(f"RSI={rsi:.0f}")
            else:
                buy = False

            if vol_ratio >= self.params['vol_ratio_min']:
                reasons.append(f"量比={vol_ratio:.1f}")
            else:
                buy = False

            if buy:
                confidence = 0.7 + (rsi / 100) * 0.2
                signals.append(Signal(
                    date=date, code=code, direction='buy',
                    price=close, volume=0, weight=1.0,
                    source=self.name, reason='; '.join(reasons),
                    confidence=min(confidence, 0.95)
                ))

        return signals

    def _get_factor(self, code: str, factor_name: str, date: str):
        if self.feature:
            return self.feature.get_factor(code, factor_name, date)
        return None