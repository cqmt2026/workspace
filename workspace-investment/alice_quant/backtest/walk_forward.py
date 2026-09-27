"""Walk-Forward 滚动回测

把历史数据分成多段训练/验证窗口，模拟策略在真实环境中的表现。
"""
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field

from ..core.result import BacktestResult
from ..core.context import Context


@dataclass
class WalkForwardConfig:
    """Walk-Forward 配置"""
    train_window: int = 120       # 训练窗口天数
    val_window: int = 30          # 验证窗口天数
    step_size: int = 30           # 滚动步长
    min_train: int = 60           # 最小训练天数


@dataclass
class WalkForwardResult:
    """Walk-Forward 结果"""
    windows: List[dict] = field(default_factory=list)
    overall_metrics: dict = field(default_factory=dict)
    strategy_params: List[dict] = field(default_factory=list)
    is_significant: bool = False

    def summary(self) -> str:
        """文本摘要"""
        n_windows = len(self.windows)
        if n_windows == 0:
            return 'Walk-Forward: 无数据'

        lines = [
            f'Walk-Forward 滚动回测 ({n_windows}个窗口)',
            f'平均收益率: {self.overall_metrics.get("avg_return", 0):.2%}',
            f'胜率: {self.overall_metrics.get("win_rate", 0):.2%}',
            f'夏普: {self.overall_metrics.get("sharpe", 0):.2f}',
            f'统计显著: {"是" if self.is_significant else "否"}',
        ]
        return '\n'.join(lines)


class WalkForwardEngine:
    """Walk-Forward 滚动回测引擎

    用法:
        wf = WalkForwardEngine()
        wf.set_dates(all_dates, start='2020-01-01', end='2026-06-30')
        wf.set_train_fn(lambda dates, params: train_model(dates))
        wf.set_eval_fn(lambda dates, params: evaluate_model(dates))
        result = wf.run()
    """

    def __init__(self, config: Optional[WalkForwardConfig] = None):
        self._config = config or WalkForwardConfig()
        self._all_dates: List[str] = []
        self._train_fn: Optional[Callable] = None
        self._eval_fn: Optional[Callable] = None
        self._params: Dict[str, Any] = {}

    def set_dates(self, all_dates: List[str],
                  start: str = '', end: str = ''):
        """设置日期范围"""
        self._all_dates = all_dates
        if start:
            self._all_dates = [d for d in all_dates if d >= start]
        if end:
            self._all_dates = [d for d in self._all_dates if d <= end]

    def set_train_fn(self, fn: Callable[[List[str], dict], Any]):
        """设置训练函数 fn(train_dates, params) -> model"""
        self._train_fn = fn

    def set_eval_fn(self, fn: Callable[[List[str], Any], float]):
        """设置评估函数 fn(eval_dates, model) -> score"""
        self._eval_fn = fn

    def set_params(self, params: Dict[str, Any]):
        """设置策略参数"""
        self._params = params

    def run(self) -> WalkForwardResult:
        """执行滚动回测"""
        if not self._all_dates:
            return WalkForwardResult()

        dates = self._all_dates
        tw = self._config.train_window
        vw = self._config.val_window
        ss = self._config.step_size

        result = WalkForwardResult()
        window_scores = []

        for i in range(0, len(dates) - tw - vw, ss):
            train_end = i + tw
            val_end = train_end + vw

            train_dates = dates[i:train_end]
            val_dates = dates[train_end:val_end]

            if len(train_dates) < self._config.min_train:
                continue
            if len(val_dates) < 5:
                continue

            # 训练
            model = None
            if self._train_fn:
                try:
                    model = self._train_fn(train_dates, self._params)
                except Exception:
                    continue

            # 验证
            score = 0.0
            if self._eval_fn and model is not None:
                try:
                    score = self._eval_fn(val_dates, model)
                except Exception:
                    continue

            window = {
                'window': len(result.windows) + 1,
                'train_start': train_dates[0],
                'train_end': train_dates[-1],
                'val_start': val_dates[0],
                'val_end': val_dates[-1],
                'train_days': len(train_dates),
                'val_days': len(val_dates),
                'score': score,
                'params': dict(self._params),
            }
            result.windows.append(window)
            window_scores.append(score)

        # 统计
        if window_scores:
            import numpy as np
            scores = np.array(window_scores)
            result.overall_metrics = {
                'avg_return': float(np.mean(scores)),
                'win_rate': float(np.mean(scores > 0)),
                'sharpe': float(np.mean(scores) / (np.std(scores) + 1e-9)),
                'n_windows': len(window_scores),
                'max_score': float(np.max(scores)),
                'min_score': float(np.min(scores)),
            }
            from scipy import stats
            t_stat, p_val = stats.ttest_1samp(scores, 0)
            result.is_significant = p_val < 0.05

        return result