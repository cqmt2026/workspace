"""策略基类 - 所有策略必须继承此类

内置因子缓存(LRU)、置信度校准、依赖声明。
策略只输出买卖信号，不计算仓位。
"""
from typing import List, Optional
from ..core.signal import Signal
from ..core.context import Context


class BaseStrategy:
    """策略基类"""

    def __init__(self, name: str, params: dict, feature_engine=None, logger=None):
        self.name = name
        self.params = params
        self.feature = feature_engine
        self.logger = logger
        self._factor_cache: dict = {}
        self._cache_order: list = []
        self._cache_max_size = 100000  # 最大缓存条目数
        self.signals: List[Signal] = []
        self.metrics: dict = {}
        self.depends_on: List[str] = []  # 依赖的策略列表

    def on_start(self, context: Context):
        """策略启动时调用

        子类在此声明股票池和预加载因子。
        """
        pass

    def on_bar(self, data, context: Context) -> List[Signal]:
        """每根K线回调

        Args:
            data: 当前K线数据
            context: 回测上下文

        Returns:
            信号列表 (volume=0表示由组合管理器决定仓位)
        """
        raise NotImplementedError

    def on_end(self, context: Context):
        """策略结束时调用"""
        pass

    def prefetch_factors(self, codes: list, factor_names: list, dates: list):
        """预加载因子到缓存"""
        if not self.feature:
            return
        for code in codes:
            for name in factor_names:
                for date in dates:
                    key = f"{code}_{name}_{date}"
                    if key not in self._factor_cache:
                        try:
                            value = self.feature.get_factor(code, name, date)
                            self._set_cache(key, value)
                        except Exception:
                            pass

    def get_cached_factor(self, code: str, factor_name: str, date: str):
        """从缓存获取因子"""
        key = f"{code}_{factor_name}_{date}"
        if key in self._factor_cache:
            # 更新LRU
            self._cache_order.remove(key)
            self._cache_order.append(key)
            return self._factor_cache[key]

        # 缓存未命中，从feature获取
        if self.feature:
            try:
                value = self.feature.get_factor(code, factor_name, date)
                self._set_cache(key, value)
                return value
            except Exception:
                return None
        return None

    def get_confidence(self, signal: Signal) -> float:
        """标准化置信度输出 (0~1)

        子类可重写此方法自定义置信度计算。
        """
        return signal.confidence

    def _set_cache(self, key: str, value):
        """设置缓存（LRU淘汰）"""
        if len(self._cache_order) >= self._cache_max_size:
            oldest = self._cache_order.pop(0)
            self._factor_cache.pop(oldest, None)
        self._factor_cache[key] = value
        self._cache_order.append(key)