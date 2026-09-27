"""回测引擎 - 事件循环

数据流：
  1. DataHub.get_bars_batch() 批量获取所有候选股票当日K线
  2. on_bar() 收到真实行情数据
  3. 策略通过 get_cached_factor() 获取因子值
  4. 仓位计算统一在 _signal_to_order() 中
  5. 止损独立于策略信号
"""
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

    def __init__(self, config=None, datahub=None, feature_engine=None, logger=None):
        self._config = config or ConfigManager()
        self._datahub = datahub
        self._feature_engine = feature_engine
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

        # 数据缓存（按日缓存所有候选股票行情）
        self._daily_bars_cache: Dict[str, Dict[str, Any]] = {}

    def run(self, strategy: BaseStrategy, start: str, end: str,
            initial_capital: float = 1000000,
            data_version: Optional[str] = None,
            watch_codes: Optional[List[str]] = None) -> BacktestResult:
        """运行回测

        Args:
            strategy: 策略实例
            start: 回测开始日期 (YYYY-MM-DD)
            end: 回测结束日期 (YYYY-MM-DD)
            initial_capital: 初始资金
            data_version: 数据版本号
            watch_codes: 候选股票列表。不传则从策略的watch_codes获取

        Returns:
            BacktestResult
        """
        self._logger.info("回测开始", strategy=strategy.name, start=start, end=end)

        # 获取交易日历
        self._all_dates = self._get_trade_dates(start, end)
        if not self._all_dates:
            raise ValueError("无交易日数据")

        # 候选股票
        watch_codes = watch_codes or getattr(strategy, 'watch_codes', []) or []

        # 策略设置FeatureEngine
        if self._feature_engine and hasattr(strategy, 'feature'):
            strategy.feature = self._feature_engine

        # 初始化账户
        account = self._account_manager.initialize(initial_capital)
        context = Context(
            current_date='', all_dates=self._all_dates,
            start_date=start, end_date=end,
            watch_codes=watch_codes,
            account=account, data_version=data_version or '',
            is_backtesting=True
        )

        # 策略启动
        strategy.on_start(context)
        self._is_running = True
        trades = []

        # 预计算所有因子（FeatureEngine在回测开始时一次性完成）
        if self._feature_engine and watch_codes:
            self._feature_engine.precompute_all(watch_codes, self._all_dates)

        # 回测主循环
        for date in tqdm(self._all_dates, desc=f"回测 {strategy.name}"):
            if not self._is_running:
                break

            self._current_date = date
            context.current_date = date

            # 获取当日所有候选股票的行情数据
            bars = self._get_daily_bars(watch_codes, date)

            # 更新持仓市值
            for code, pos in list(account.positions.items()):
                if code in bars:
                    pos.current_price = bars[code].get('close', pos.current_price)
                pos.update_market_value(pos.current_price)
                pos.days_held += 1

            # 止损检查（独立于策略）
            stop_signals = self._check_stop_loss(account, date)
            for s in stop_signals:
                order = self._signal_to_order(s, account, date, bars)
                if order:
                    filled = self._order_manager.execute(order, bars.get(s.code, {}), date)
                    if filled:
                        # 卖出前算盈亏
                        trade = self._order_to_trade(filled, s)
                        if filled.direction == 'sell':
                            trade['profit'] = self._calc_profit(filled, account)
                        self._account_manager.apply_order(filled, account)
                        trades.append(trade)

            # 执行策略
            signals = strategy.on_bar(bars, context)
            if signals:
                strategy.signals.extend(signals)

            # 市场状态动态持仓上限
            max_positions = self._get_config('risk.max_positions', 5)
            # 策略可以覆盖
            if hasattr(strategy, 'params') and 'max_positions_bear' in strategy.params:
                is_bear = getattr(strategy, '_last_market_status', '') == 'bear'
                if is_bear:
                    max_positions = strategy.params.get('max_positions_bear', max_positions)

            for signal in signals:
                if signal.direction == 'close':
                    for code, pos in list(account.positions.items()):
                        s = Signal(date=date, code=code, direction='sell',
                                   price=bars.get(code, {}).get('close', signal.price),
                                   volume=pos.volume,
                                   source=signal.source, reason=signal.reason, confidence=1.0)
                        order = self._signal_to_order(s, account, date, bars)
                        if order:
                            filled = self._order_manager.execute(order, bars.get(code, {}), date)
                            if filled:
                                trade = self._order_to_trade(filled, s)
                                if filled.direction == 'sell':
                                    trade['profit'] = self._calc_profit(filled, account)
                                self._account_manager.apply_order(filled, account)
                                trades.append(trade)
                else:
                    # 总持仓上限检查
                    max_positions = self._get_config('risk.max_positions', 5)
                    if signal.direction == 'buy' and max_positions > 0:
                        if len(account.positions) >= max_positions:
                            continue
                    order = self._signal_to_order(signal, account, date, bars)
                    if order:
                        filled = self._order_manager.execute(order, bars.get(signal.code, {}), date)
                        if filled:
                            trade = self._order_to_trade(filled, signal)
                            if filled.direction == 'sell':
                                trade['profit'] = self._calc_profit(filled, account)
                            self._account_manager.apply_order(filled, account)
                            trades.append(trade)

            # 更新账户
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
        """停止回测"""
        self._is_running = False

    def _get_daily_bars(self, codes: List[str], date: str) -> Dict[str, Dict[str, Any]]:
        """获取当日所有候选股票的行情数据

        优先从DataHub批量获取，回退到缓存。

        Returns:
            {code: {'date': str, 'open': float, 'close': float, 'high': float, 'low': float, 'volume': float}}
        """
        if not codes:
            return {}

        result = {}

        # 从DataHub批量获取
        if self._datahub:
            try:
                batch = self._datahub.get_bars_batch(codes, date, date, '1d', snapshot_date=date)
                if batch:
                    for code, df in batch.items():
                        if df is not None and not df.empty:
                            row = df.iloc[-1]
                            result[code] = {
                                'date': row.get('date', date),
                                'open': float(row.get('open', 0)),
                                'close': float(row.get('close', 0)),
                                'high': float(row.get('high', 0)),
                                'low': float(row.get('low', 0)),
                                'volume': float(row.get('volume', 0)),
                            }
            except Exception as e:
                self._logger.debug(f"批量获取行情失败", date=date, error=str(e))

        # 补充缺失的股票（用0填充）
        for code in codes:
            if code not in result:
                result[code] = {
                    'date': date,
                    'open': 0, 'close': 0, 'high': 0, 'low': 0, 'volume': 0,
                }

        return result

    def _check_stop_loss(self, account: Account, date: str) -> List[Signal]:
        """止损检查

        独立于策略信号，由回测引擎统一执行。
        """
        signals = []

        stop_loss_pct = self._get_config('risk.stop_loss', 0.05)
        for code, pos in list(account.positions.items()):
            if pos.profit_pct <= -stop_loss_pct:
                signals.append(Signal(
                    date=date, code=code, direction='sell',
                    price=pos.current_price, volume=pos.volume,
                    source='risk_control', reason=f'止损({pos.profit_pct:.1%})',
                    confidence=1.0
                ))

        max_drawdown = self._get_config('risk.portfolio_stop', 0.15)
        total_return = account.total_return()
        if total_return <= -max_drawdown:
            for code, pos in list(account.positions.items()):
                signals.append(Signal(
                    date=date, code=code, direction='sell',
                    price=pos.current_price, volume=pos.volume,
                    source='risk_control', reason=f'最大回撤止损({total_return:.1%})',
                    confidence=1.0
                ))

        return signals

    def _signal_to_order(self, signal: Signal, account: Account, date: str,
                         bars: Dict[str, Dict] = None) -> Optional[Order]:
        """信号转订单 — 仓位计算唯一入口

        Args:
            signal: 策略信号
            account: 账户状态
            date: 日期
            bars: 当日行情数据（用于获取成交价）
        """
        bars = bars or {}

        if signal.direction == 'buy':
            if signal.volume > 0:
                volume = signal.volume
            else:
                max_single = self._get_config('risk.max_single_position', 0.20)
                max_cash_ratio = self._get_config('risk.min_cash_ratio', 0.05)
                target_value = account.total_value * max_single * signal.weight
                available = account.cash * (1 - max_cash_ratio)
                target_value = min(target_value, available)

                price = signal.price if signal.price > 0 else bars.get(signal.code, {}).get('close', 10.0)
                if price <= 0:
                    price = 10.0
                volume = int(target_value / price / 100) * 100

            if volume <= 0:
                return None

            price = signal.price if signal.price > 0 else bars.get(signal.code, {}).get('close', 10.0)
            if price <= 0:
                price = 10.0

            return Order(
                order_id=f"O{date}{signal.code}",
                date=date, code=signal.code,
                direction='buy', price=price, volume=volume,
                source=signal.source, reason=signal.reason,
                risk_check=signal.risk_check
            )

        elif signal.direction == 'sell':
            pos = account.get_position(signal.code)
            if not pos or pos.volume <= 0:
                return None
            volume = signal.volume if signal.volume > 0 else pos.volume
            price = signal.price if signal.price > 0 else bars.get(signal.code, {}).get('close', pos.current_price)
            if price <= 0:
                price = pos.current_price
            return Order(
                order_id=f"O{date}{signal.code}",
                date=date, code=signal.code,
                direction='sell', price=price, volume=min(volume, pos.volume),
                source=signal.source, reason=signal.reason,
                risk_check=signal.risk_check
            )

        return None

    def _calc_profit(self, order: Order, account: Account) -> float:
        """计算卖出订单的盈亏

        卖出价 - 买入均价（从持仓记录获取）× 卖出数量
        """
        if order.direction != 'sell':
            return 0
        pos = account.get_position(order.code)
        if pos and pos.avg_cost > 0:
            return (order.filled_price - pos.avg_cost) * order.filled_volume
        return 0

    def _order_to_trade(self, order: Order, signal: Signal) -> dict:
        """订单转交易记录

        profit在回测循环中由调用方设置（从持仓获取买入成本）。
        这里默认设为0。
        """
        return {
            'date': order.date,
            'code': order.code,
            'direction': order.direction,
            'price': order.filled_price,
            'volume': order.filled_volume,
            'value': order.fill_value(),
            'commission': order.commission,
            'tax': order.tax,
            'slippage': order.slippage,
            'source': signal.source,
            'reason': signal.reason,
            'profit': 0,
        }

    def _get_trade_dates(self, start: str, end: str) -> List[str]:
        """获取交易日列表"""
        if self._datahub:
            try:
                calendar = self._datahub.get_trade_calendar()
                if calendar:
                    return [d for d in calendar if start <= d <= end]
            except Exception:
                pass
        dates = []
        current = datetime.strptime(start, '%Y-%m-%d')
        end_dt = datetime.strptime(end, '%Y-%m-%d')
        while current <= end_dt:
            if current.weekday() < 5:
                dates.append(current.strftime('%Y-%m-%d'))
            current += pd.Timedelta(days=1)
        return dates

    def _get_config(self, key: str, default: Any) -> Any:
        if self._config:
            return self._config.get(key, default)
        return default