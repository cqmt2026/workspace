"""组合管理器 - 独立层

介于Strategy和Backtest/Execute之间。
职责：策略依赖解析、信号融合、仓位计算、资金管理、风险预算。
"""
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd

from ..core.signal import Signal
from ..core.account import Account
from ..core.context import Context
from ..core.exceptions import CircularDependencyError


class PortfolioManager:
    """组合管理器"""

    def __init__(self, config=None, logger=None):
        self._config = config
        self._logger = logger
        self._strategies: Dict[str, dict] = {}  # {name: {strategy, weight}}
        self._execution_order: List[str] = []

    def add_strategy(self, strategy, weight: float = 1.0):
        """添加策略

        Args:
            strategy: 策略实例
            weight: 策略权重
        """
        self._strategies[strategy.name] = {
            'strategy': strategy,
            'weight': weight,
        }

    def remove_strategy(self, name: str):
        """移除策略"""
        if name in self._strategies:
            del self._strategies[name]

    def resolve_execution_order(self) -> List[str]:
        """解析策略执行顺序

        使用拓扑排序确定策略执行顺序。
        无依赖的策略先执行，有依赖的后执行。

        Returns:
            策略名称列表（执行顺序）
        """
        # 构建依赖图
        graph = {}
        for name, info in self._strategies.items():
            strategy = info['strategy']
            graph[name] = getattr(strategy, 'depends_on', [])

        # 拓扑排序
        order = []
        visited = set()
        temp = set()

        def visit(name):
            if name in temp:
                raise CircularDependencyError(f"策略循环依赖: {name}")
            if name not in visited:
                temp.add(name)
                for dep in graph.get(name, []):
                    if dep in graph:
                        visit(dep)
                temp.remove(name)
                visited.add(name)
                order.append(name)

        for name in graph:
            if name not in visited:
                visit(name)

        self._execution_order = order
        return order

    def get_portfolio_signal(self, date: str, account: Account,
                             context: Context) -> List[Signal]:
        """获取组合信号

        1. 按依赖顺序执行所有策略
        2. 融合所有策略信号
        3. 计算具体仓位

        Args:
            date: 当前日期
            account: 账户状态
            context: 回测上下文

        Returns:
            含具体仓位的信号列表
        """
        all_signals = []

        # 1. 按依赖顺序执行策略
        for name in self._execution_order:
            if name not in self._strategies:
                continue
            strategy = self._strategies[name]['strategy']
            signals = strategy.on_bar({'date': date}, context)
            all_signals.extend(signals)

        # 2. 信号融合
        fused_signals = self._fuse_signals(all_signals)

        # 3. 计算仓位
        result = []
        for signal in fused_signals:
            signal_with_position = self._calculate_position(signal, account)
            if signal_with_position:
                result.append(signal_with_position)

        return result

    def get_strategy_correlation(self) -> pd.DataFrame:
        """计算策略相关性

        Returns:
            相关性矩阵 DataFrame
        """
        import pandas as pd
        names = list(self._strategies.keys())
        # 简化版：返回单位矩阵
        return pd.DataFrame(np.eye(len(names)), index=names, columns=names)

    def _fuse_signals(self, signals: List[Signal]) -> List[Signal]:
        """信号融合

        规则:
          - 同一股票多个买入信号：取置信度最高的
          - 买入和卖出冲突：按优先级处理
          - 连续多日相同信号：去重
        """
        if not signals:
            return []

        # 按股票分组
        signal_map: Dict[str, Signal] = {}
        for s in signals:
            if s.code not in signal_map or s.confidence > signal_map[s.code].confidence:
                signal_map[s.code] = s

        return list(signal_map.values())

    def _calculate_position(self, signal: Signal, account: Account) -> Optional[Signal]:
        """计算具体仓位

        由组合管理器统一计算，策略只输出方向和置信度。

        Args:
            signal: 策略信号 (volume=0)
            account: 账户状态

        Returns:
            含具体仓位的信号 (volume>0)
        """
        if signal.volume > 0:
            return signal  # 已有具体仓位

        # 获取配置
        max_single = self._get_config('risk.max_single_position', 0.20)
        max_cash_ratio = self._get_config('risk.min_cash_ratio', 0.05)

        # 计算目标市值
        target_value = account.total_value * max_single * signal.weight

        # 检查可用资金
        available = account.cash * (1 - max_cash_ratio)
        target_value = min(target_value, available)

        # 计算股数（100的整数倍）
        if signal.price <= 0:
            return None
        volume = int(target_value / signal.price / 100) * 100

        if volume <= 0:
            return None

        signal.volume = volume
        return signal

    def _get_config(self, key: str, default: Any) -> Any:
        if self._config:
            return self._config.get(key, default)
        return default