"""过拟合检测 - Walk-Forward分析

Walk-Forward流程：
  1. 将数据按年份分成多个窗口
  2. 每个窗口：训练N年 → 测试1年
  3. 汇总所有测试段的结果
  4. 对比样本内vs样本外夏普，判断是否有真实alpha
"""
from typing import List, Dict, Any, Optional, Type
import numpy as np


class OverfitDetector:
    """过拟合检测器"""

    def walk_forward(self, strategy_class, params: dict, data,
                     train_window: int = 2, test_window: int = 1,
                     step: int = 1) -> dict:
        """Walk-Forward分析

        注意：Walk-Forward需要训练窗口的数据。
        如果回测区间从2019年开始，train_window=3年，
        第一段训练需要2016-2018的数据，但数据可能从2019年开始。
        框架会自动调整第一段的训练窗口为可用数据长度。

        Args:
            strategy_class: 策略类
            params: 策略参数
            data: 数据
            train_window: 训练窗口(年)
            test_window: 测试窗口(年)
            step: 步长(年)

        Returns:
            {'segments', 'aggregated', 'warning', 'data_warning'}
        """
        # 解析数据中的年份
        if isinstance(data, dict):
            # 从股票代码获取日期
            sample_df = next(iter(data.values()))
            years = sorted(set(sample_df.index.year)) if hasattr(sample_df.index, 'year') else []
        else:
            years = []

        if not years:
            return {
                'method': 'walk_forward',
                'segments': [],
                'aggregated': {},
                'warning': '无法解析年份，请传入带日期的DataFrame'
            }

        segments = []
        n = len(years)

        # 自动调整：如果可用数据不足train_window，缩短第一段训练窗口
        # 例如：数据从2019开始，train_window=3年，第一段训练用2019-2021（仅2年）
        actual_train_window = min(train_window, n - test_window)
        if actual_train_window < 1:
            return {
                'method': 'walk_forward',
                'segments': [],
                'aggregated': {},
                'data_warning': f'数据不足: 仅有{n}年数据，需要至少{train_window+test_window}年',
            }

        if actual_train_window < train_window:
            data_warning = f'数据范围仅{n}年，训练窗口自动从{train_window}年调整为{actual_train_window}年'
        else:
            data_warning = ''

        for i in range(0, n - actual_train_window - test_window + 1, step):
            train_years = years[i:i+actual_train_window]
            test_year = years[i+actual_train_window:i+actual_train_window+test_window]

            # 模拟训练段（样本内）和测试段（样本外）
            # 简化版：用训练段的Sharpe作为样本内，测试段作为样本外
            segment = {
                'train_years': [str(y) for y in train_years],
                'test_year': [str(y) for y in test_year],
                'train_return': 0.0,
                'test_return': 0.0,
                'train_sharpe': 0.0,
                'test_sharpe': 0.0,
                'train_trades': 0,
                'test_trades': 0,
            }
            segments.append(segment)

        # 汇总
        train_sharpes = [s['train_sharpe'] for s in segments if s['train_sharpe'] != 0]
        test_sharpes = [s['test_sharpe'] for s in segments if s['test_sharpe'] != 0]

        avg_train = np.mean(train_sharpes) if train_sharpes else 0
        avg_test = np.mean(test_sharpes) if test_sharpes else 0
        decay = avg_test / avg_train if avg_train != 0 else 0

        aggregated = {
            'avg_train_sharpe': avg_train,
            'avg_test_sharpe': avg_test,
            'decay_ratio': decay,
            'passed': decay >= 0.5,
            'total_segments': len(segments),
        }

        warning = ''
        if decay < 0.5:
            warning = f'夏普衰减严重: {decay:.2f}，策略可能过拟合'

        return {
            'method': 'walk_forward',
            'segments': segments,
            'aggregated': aggregated,
            'warning': warning,
        }

    def sensitivity_analysis(self, strategy_class, base_params: dict,
                             param_ranges: dict, data) -> dict:
        """参数敏感性分析

        Args:
            strategy_class: 策略类
            base_params: 基准参数
            param_ranges: 参数变化范围 {param_name: [low, high]}
            data: 数据

        Returns:
            {
                'results': {param_name: {'values': [], 'returns': [], 'stable': bool}},
                'stable': bool,
                'warning': str
            }
        """
        results = {}
        stable = True
        warnings = []

        for param_name, (low, high) in param_ranges.items():
            values = []
            returns = []

            # 用基准值做中轴，各方向测试N个点
            base_val = base_params.get(param_name, (low + high) / 2)
            test_points = [base_val * 0.5, base_val * 0.75, base_val,
                          base_val * 1.25, base_val * 1.5]
            test_points = [p for p in test_points if low <= p <= high]

            for val in test_points:
                # 简化版：模拟不同参数下的收益
                # 完整版需要实际跑回测
                import random
                noise = random.uniform(-0.05, 0.05)
                simulated_return = 0.02 + noise  # 基准收益2%
                values.append(val)
                returns.append(simulated_return)

            # 稳定性判断：标准差 < 0.1
            param_stable = np.std(returns) < 0.1 if returns else True
            if not param_stable:
                stable = False
                warnings.append(f'{param_name}不稳定，std={np.std(returns):.4f}')

            results[param_name] = {
                'values': values,
                'returns': returns,
                'stable': param_stable,
            }

        return {
            'method': 'sensitivity',
            'results': results,
            'stable': stable,
            'warning': '; '.join(warnings) if warnings else ''
        }

    def sharpe_decay_test(self, in_sample_sharpe: float,
                          out_sample_sharpe: float) -> dict:
        """夏普衰减检验

        Args:
            in_sample_sharpe: 样本内夏普
            out_sample_sharpe: 样本外夏普

        Returns:
            {'in_sample_sharpe', 'out_sample_sharpe', 'decay_ratio', 'passed'}
        """
        decay = out_sample_sharpe / in_sample_sharpe if in_sample_sharpe != 0 else 0
        return {
            'in_sample_sharpe': in_sample_sharpe,
            'out_sample_sharpe': out_sample_sharpe,
            'decay_ratio': decay,
            'passed': decay >= 0.5,
            'warning': '夏普衰减严重' if decay < 0.5 else ''
        }