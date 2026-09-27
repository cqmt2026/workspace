"""风控模块 - 交易前/中/后/持仓风控"""
from typing import Dict, List, Optional, Any
from ..core.signal import Signal
from ..core.account import Account


class RiskManager:
    """风控管理器"""

    def __init__(self, config=None, logger=None):
        self._config = config
        self._logger = logger
        self._blacklist: set = set()
        self._whitelist: Optional[set] = None
        self._risk_events: List[dict] = []

    def check_before_trade(self, signal: Signal, account: Account) -> dict:
        """交易前风控检查

        Args:
            signal: 信号
            account: 账户状态

        Returns:
            {'passed': bool, 'reason': str}
        """
        checks = []

        # 1. 黑名单检查
        if self._is_blacklisted(signal.code):
            checks.append(('blacklist', False, '股票在黑名单中'))

        # 2. 白名单检查
        if self._whitelist is not None and signal.code not in self._whitelist:
            checks.append(('whitelist', False, '股票不在白名单中'))

        # 3. ST检查
        if signal.code.startswith('st'):
            checks.append(('st', False, 'ST股票'))

        # 4. 集中度检查
        if signal.direction == 'buy':
            max_single = self._get_config('risk.max_single_position', 0.20)
            target_value = signal.volume * signal.price
            current_ratio = target_value / account.total_value if account.total_value > 0 else 0
            if current_ratio > max_single:
                checks.append(('concentration', False, f'集中度超限: {current_ratio:.1%} > {max_single:.1%}'))

        # 5. 资金检查
        if signal.direction == 'buy':
            cost = signal.volume * signal.price
            if cost > account.cash:
                checks.append(('cash', False, f'资金不足: 需要{cost:.0f}, 可用{account.cash:.0f}'))

        # 汇总
        failed = [c for c in checks if not c[1]]
        if failed:
            reasons = '; '.join(c[2] for c in failed)
            event = {
                'type': 'pre_trade',
                'code': signal.code,
                'direction': signal.direction,
                'reasons': reasons,
                'signal': str(signal)
            }
            self._risk_events.append(event)
            return {'passed': False, 'reason': reasons, 'checks': checks}

        return {'passed': True, 'reason': '', 'checks': checks}

    def check_position(self, position) -> Optional[dict]:
        """持仓风控检查

        Args:
            position: 持仓对象

        Returns:
            None: 无异常 / dict: 需要执行的动作
        """
        if position is None:
            return None

        stop_loss = self._get_config('risk.stop_loss', 0.05)

        # 止损检查
        if position.profit_pct <= -stop_loss:
            return {
                'action': 'sell',
                'reason': f'止损触发: 亏损{position.profit_pct:.1%}',
                'confidence': 1.0
            }

        return None

    def add_to_blacklist(self, code: str):
        """添加到黑名单"""
        self._blacklist.add(code)

    def set_whitelist(self, codes: List[str]):
        """设置白名单"""
        self._whitelist = set(codes)

    def get_risk_events(self, limit: int = 50) -> List[dict]:
        """获取风控事件"""
        return self._risk_events[-limit:]

    def _is_blacklisted(self, code: str) -> bool:
        """检查是否在黑名单中"""
        if code in self._blacklist:
            return True
        # 退市股/ST股
        clean = code.replace('sz.', '').replace('sh.', '').replace('bj.', '')
        if clean.startswith('3') and not clean.startswith('300'):  # 老三板
            return True
        return False

    def _get_config(self, key: str, default: Any) -> Any:
        if self._config:
            return self._config.get(key, default)
        return default