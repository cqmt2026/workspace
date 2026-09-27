"""回测引擎 - 事件循环"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from tqdm import tqdm

from ..core.config import ConfigManager
from ..core.logger import Logger
from ..core.signal import Signal
from ..core.order import Order
from ..core.account import Account, Position
from ..core.context import Context
from ..core.result import BacktestResult
from ..strategies.base import BaseStrategy
from .order_manager import OrderManager
from .account_manager import AccountManager
from .commission import CommissionModel
from .slippage import SlippageModel
from .performance import PerformanceAnalyzer
from .overfitting import OverfitDetector


class BacktestEngine:
    """回测引擎"""

    def __init__(self, config=None, datahub=None, logger=None):
        self._config = config or ConfigManager()
        self._datahub = datahub
        self._logger = logger or Logger()
        self._commission = CommissionModel(self._config)
        self._slippage = SlippageModel(self._config)
        self._order_manager = OrderManager(self._config, self._commission, self._slippage)
        self._account_manager = AccountManager(self._config)
        self._performance = PerformanceAnalyzer()
        self._overfit = OverfitDetector()
        self._current_date = None
        self._all_dates = []
        self._is_running = False

    def run(self, strategy: BaseStrategy, start: str, end: str,
            initial_capital: float = 1000000,
            data_version: Optional[str] = None) -> BacktestResult:
        self._logger.info("回测开始", strategy=strategy.name, start=start, end=end)
        self._all_dates = self._get_trade_dates(start, end)
        if not self._all_dates:
            raise ValueError("无交易日数据")
        account = self._account_manager.initialize(initial_capital)
        context = Context(
            current_date='', all_dates=self._all_dates,
            start_date=start, end_date=end, watch_codes=[],
            account=account, data_version=data_version or '',
            is_backtesting=True
        )
        strategy.on_start(context)
        self._is_running = True
        trades = []

        for date in tqdm(self._all_dates, desc=f"回测 {strategy.name}"):
            if not self._is_running:
                break
            self._current_date = date
            context.current_date = date
            bar_data = {'date': date, 'close': 0, 'open': 0, 'high': 0, 'low': 0, 'volume': 0}

            self._pre_day(date, account, context)
            signals = strategy.on_bar(bar_data, context)
            if signals:
                strategy.signals.extend(signals)

            for signal in signals:
                if signal.direction == 'close':
                    for code, pos in list(account.positions.items()):
                        s = Signal(date=date, code=code, direction='sell',
                                   price=signal.price, volume=pos.volume,
                                   source=signal.source, reason=signal.reason, confidence=1.0)
                        o = self._signal_to_order(s, account, date)
                        if o:
                            f = self._order_manager.execute(o, bar_data, date)
                            if f:
                                self._account_manager.apply_order(f, account)
                                trades.append(self._order_to_trade(f, s))
                else:
                    o = self._signal_to_order(signal, account, date)
                    if o:
                        f = self._order_manager.execute(o, bar_data, date)
                        if f:
                            self._account_manager.apply_order(f, account)
                            trades.append(self._order_to_trade(f, signal))

            for code, pos in account.positions.items():
                pos.days_held += 1
                if pos.profit_pct <= -0.05:
                    s = Signal(date=date, code=code, direction='sell',
                               price=pos.current_price, volume=pos.volume,
                               source='risk_control', reason='止损', confidence=1.0)
                    o = self._signal_to_order(s, account, date)
                    if o:
                        f = self._order_manager.execute(o, bar_data, date)
                        if f:
                            self._account_manager.apply_order(f, account)
                            trades.append(self._order_to_trade(f, s))

            account.date = date
            account.total_value = account.cash + account.position_value()

        strategy.on_end(context)
        self._logger.info("回测完成", strategy=strategy.name,
                         trades=len(trades), final_value=account.total_value)
        result = self._performance.analyze(
            strategy_name=strategy.name, params=strategy.params,
            start_date=start, end_date=end, account=account,
            trades=trades, all_dates=self._all_dates,
            data_version=data_version or '')
        return result

    def stop(self):
        self._is_running = False

    def _pre_day(self, date: str, account: Account, context: Context):
        for pos in account.positions.values():
            pos.days_held += 1

    def _signal_to_order(self, signal: Signal, account: Account, date: str) -> Optional[Order]:
        if signal.direction == 'buy':
            if signal.volume > 0:
                volume = signal.volume
            else:
                target_value = account.total_value * signal.weight * 0.2
                volume = int(target_value / signal.price / 100) * 100 if signal.price > 0 else 0
            if volume <= 0:
                return None
            return Order(order_id=f"O{date}{signal.code}", date=date, code=signal.code,
                         direction='buy', price=signal.price, volume=volume,
                         source=signal.source, reason=signal.reason)
        elif signal.direction == 'sell':
            pos = account.get_position(signal.code)
            if not pos or pos.volume <= 0:
                return None
            return Order(order_id=f"O{date}{signal.code}", date=date, code=signal.code,
                         direction='sell', price=signal.price, volume=signal.volume or pos.volume,
                         source=signal.source, reason=signal.reason)
        return None

    def _order_to_trade(self, order: Order, signal: Signal) -> dict:
        return {'date': order.date, 'code': order.code, 'direction': order.direction,
                'price': order.filled_price, 'volume': order.filled_volume,
                'value': order.fill_value(), 'commission': order.commission,
                'tax': order.tax, 'slippage': order.slippage,
                'source': signal.source, 'reason': signal.reason}

    def _get_trade_dates(self, start: str, end: str) -> List[str]:
        if self._datahub:
            calendar = self._datahub.get_trade_calendar()
            if calendar:
                return [d for d in calendar if start <= d <= end]
        dates = []
        current = datetime.strptime(start, '%Y-%m-%d')
        end_dt = datetime.strptime(end, '%Y-%m-%d')
        while current <= end_dt:
            if current.weekday() < 5:
                dates.append(current.strftime('%Y-%m-%d'))
            current += pd.Timedelta(days=1)
        return dates