"""执行层 - 信号处理器"""
from typing import List, Optional, Dict, Any
from ..core.signal import Signal
from ..core.order import Order
from ..core.account import Account
from .risk_manager import RiskManager


class SignalHandler:
    """信号处理器

    接收策略/组合信号 → 预处理 → 风控检查 → 生成订单
    """

    def __init__(self, config=None, logger=None):
        self._config = config
        self._logger = logger
        self._risk_manager = RiskManager(config, logger)
        self._signal_history: List[Signal] = []
        self._silent_period: Dict[str, int] = {}  # {code: last_signal_date}

    def process(self, signals: List[Signal], account: Account,
                date: str) -> List[Order]:
        """处理信号

        Args:
            signals: 信号列表
            account: 账户状态
            date: 当前日期

        Returns:
            订单列表
        """
        if not signals:
            return []

        orders = []

        # 1. 信号预处理
        signals = self._preprocess(signals, date)

        # 2. 风控检查 + 生成订单
        for signal in signals:
            # 风控检查
            risk_check = self._risk_manager.check_before_trade(signal, account)
            signal.risk_check = risk_check

            if not risk_check.get('passed', True):
                self._log_warning(f"风控拒绝", code=signal.code, reason=risk_check.get('reason'))
                continue

            # 生成订单
            order = self._create_order(signal, date)
            if order:
                orders.append(order)
                self._signal_history.append(signal)

        return orders

    def _preprocess(self, signals: List[Signal], date: str) -> List[Signal]:
        """信号预处理

        1. 去重：同一股票只保留置信度最高的信号
        2. 优先级：P0人工 > P1风控 > P2组合 > P3单策略
        3. 静默期：相同信号在N分钟内不重复发送
        """
        if not signals:
            return []

        # 按优先级排序
        priority_map = {'manual': 0, 'risk_control': 1, 'portfolio': 2}
        signals.sort(key=lambda s: priority_map.get(s.source, 3))

        # 按股票去重
        signal_map = {}
        for s in signals:
            if s.code in signal_map:
                # 保留优先级更高的
                existing = signal_map[s.code]
                if priority_map.get(s.source, 3) < priority_map.get(existing.source, 3):
                    signal_map[s.code] = s
            else:
                signal_map[s.code] = s

        # 静默期检查
        result = []
        for code, signal in signal_map.items():
            if code in self._silent_period:
                if self._silent_period[code] == date:
                    continue  # 同一日不重复发送
            self._silent_period[code] = date
            result.append(signal)

        return result

    def _create_order(self, signal: Signal, date: str) -> Optional[Order]:
        """信号转订单"""
        if signal.volume <= 0:
            return None

        return Order(
            order_id=f"O{date.replace('-', '')}_{signal.code}_{hash(signal.reason) % 10000:04d}",
            date=date,
            code=signal.code,
            direction=signal.direction,
            price=signal.price,
            volume=signal.volume,
            source=signal.source,
            reason=signal.reason,
            risk_check=signal.risk_check
        )

    def _log_warning(self, msg: str, **kwargs):
        if self._logger:
            self._logger.warning(msg, **kwargs)