"""模拟交易 - Paper Trading"""
import os
import json
from datetime import datetime
from typing import List, Optional, Dict
from ..core.account import Account, Position
from ..core.order import Order
from ..core.signal import Signal
from ..backtest.account_manager import AccountManager
from ..backtest.order_manager import OrderManager
from ..backtest.commission import CommissionModel
from ..backtest.slippage import SlippageModel


class PaperTrading:
    """模拟交易

    和回测共用账户模型和订单管理。
    """

    def __init__(self, config=None, logger=None):
        self._config = config
        self._logger = logger
        self._account_manager = AccountManager(config)
        self._commission = CommissionModel(config)
        self._slippage = SlippageModel(config)
        self._order_manager = OrderManager(config, self._commission, self._slippage)
        self._account: Optional[Account] = None
        self._trade_log: List[dict] = []
        self._output_dir = self._get_output_dir()

    def initialize(self, initial_capital: float = 1000000):
        """初始化模拟交易"""
        self._account = self._account_manager.initialize(initial_capital)
        self._log_info(f"模拟交易初始化", capital=initial_capital)

    def execute(self, signals: List[Signal], market_data: dict,
                date: str) -> List[Order]:
        """执行交易

        Args:
            signals: 信号列表
            market_data: 市场数据
            date: 日期

        Returns:
            成交订单列表
        """
        if self._account is None:
            raise ValueError("模拟交易未初始化")

        filled_orders = []

        for signal in signals:
            order = Order(
                order_id=f"P{date.replace('-', '')}_{signal.code}",
                date=date,
                code=signal.code,
                direction=signal.direction,
                price=signal.price,
                volume=signal.volume,
                source=signal.source,
                reason=signal.reason
            )

            filled = self._order_manager.execute(order, market_data, date)
            if filled:
                self._account_manager.apply_order(filled, self._account)
                self._log_trade(filled, signal)
                filled_orders.append(filled)

        return filled_orders

    def get_account(self) -> Optional[Account]:
        """获取账户状态"""
        return self._account

    def get_trade_history(self, limit: int = 100) -> List[dict]:
        """获取交易历史"""
        return self._trade_log[-limit:]

    def save_state(self):
        """保存状态"""
        if not self._output_dir:
            return
        os.makedirs(self._output_dir, exist_ok=True)

        # 保存账户
        state = {
            'date': self._account.date if self._account else '',
            'total_value': self._account.total_value if self._account else 0,
            'cash': self._account.cash if self._account else 0,
            'positions': {
                code: {
                    'volume': pos.volume,
                    'avg_cost': pos.avg_cost,
                    'current_price': pos.current_price
                }
                for code, pos in (self._account.positions.items() if self._account else {})
            },
            'trade_log': self._trade_log[-100:],
        }

        path = os.path.join(self._output_dir, 'paper_state.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _log_trade(self, order: Order, signal: Signal):
        """记录交易"""
        trade = {
            'date': order.date,
            'code': order.code,
            'direction': order.direction,
            'price': order.filled_price,
            'volume': order.filled_volume,
            'value': order.fill_value(),
            'commission': order.commission,
            'tax': order.tax,
            'source': signal.source,
            'reason': signal.reason,
        }
        self._trade_log.append(trade)

    def _log_info(self, msg: str, **kwargs):
        if self._logger:
            self._logger.info(msg, **kwargs)

    def _get_output_dir(self) -> str:
        if self._config:
            d = self._config.get('paper_trading.output_dir', '')
            if d:
                return d
        return os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'data', 'paper_trading')