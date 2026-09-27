# -*- coding: utf-8 -*-
"""
多策略定义 - 基于不同信号组合
包含：趋势跟踪/均值回归/突破/动量/反转等策略
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging; logger = logging

class MeanReversionStrategy:
    """均值回归策略"""
    
    def __init__(self, name: str = '均值回归 v1', config: Dict = None):
        self.name = name
        self.config = config or {}
        self.position = 0
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit = 0
    
    def check_entry_condition(self, signals: Dict) -> bool:
        """
        入场条件：
        1. 价格在布林带下轨附近 (bb_position < 0.2)
        2. 出现极端下跌 (z_score < -2)
        3. 波动率正常或上升
        """
        volatility = signals.get('volatility', {})
        anomaly = signals.get('anomaly', {})
        
        # 条件 1: 价格在布林带下轨附近
        if volatility.get('bb_position', 1) > 0.2:
            return False
        
        # 条件 2: 出现极端下跌
        if anomaly.get('return_zscore', 0) > -2:
            return False
        
        # 条件 3: 波动率正常或上升
        vol_signal = volatility.get('vol_signal', '')
        if vol_signal == '高风险':
            return False
        
        print("均值回归策略：满足入场条件")
        return True
    
    def check_exit_condition(self, signals: Dict, current_price: float) -> bool:
        """
        出场条件：
        1. 价格回归到布林带中轨以上 (bb_position > 0.5)
        2. 趋势转强 (trend_score >= 2)
        """
        volatility = signals.get('volatility', {})
        trend = signals.get('trend', {})
        
        # 条件 1: 价格回归到布林带中轨以上
        if volatility.get('bb_position', 0) > 0.5:
            print("均值回归策略：价格回归，出场")
            return True
        
        # 条件 2: 趋势转强
        if trend.get('trend_score', 0) >= 2:
            print("均值回归策略：趋势转强，出场")
            return True
        
        return False
    
    def check_strategy_invalid(self, signals: Dict) -> bool:
        """策略失效条件"""
        trend = signals.get('trend', {})
        volatility = signals.get('volatility', {})
        
        # 强势单边趋势
        if abs(trend.get('trend_score', 0)) >= 3:
            print("均值回归策略：强势单边趋势，策略失效")
            return True
        
        # 波动率压缩
        if volatility.get('vol_state') == '波动率压缩':
            print("均值回归策略：波动率压缩，策略失效")
            return True
        
        return False


class BreakoutStrategy:
    """突破策略"""
    
    def __init__(self, name: str = '突破策略 v1', config: Dict = None):
        self.name = name
        self.config = config or {}
        self.position = 0
        self.entry_price = 0
    
    def check_entry_condition(self, signals: Dict) -> bool:
        """
        入场条件：
        1. 创 N 日新高 (new_high = True)
        2. 放量 (volume_ratio > 1.5)
        3. 趋势强劲 (trend_score >= 2)
        """
        anomaly = signals.get('anomaly', {})
        volume = signals.get('volume', {})
        trend = signals.get('trend', {})
        
        # 条件 1: 创 N 日新高
        if not anomaly.get('new_high', False):
            return False
        
        # 条件 2: 放量
        if volume.get('volume_ratio', 1) < 1.5:
            return False
        
        # 条件 3: 趋势强劲
        if trend.get('trend_score', 0) < 2:
            return False
        
        print("突破策略：满足入场条件")
        return True
    
    def check_exit_condition(self, signals: Dict, current_price: float) -> bool:
        """
        出场条件：
        1. 跌破入场价 (止损)
        2. 趋势反转 (trend_score <= -1)
        """
        trend = signals.get('trend', {})
        
        # 条件 1: 跌破入场价
        if self.position > 0 and current_price < self.entry_price * 0.95:
            print("突破策略：跌破止损，出场")
            return True
        
        # 条件 2: 趋势反转
        if trend.get('trend_score', 0) <= -1:
            print("突破策略：趋势反转，出场")
            return True
        
        return False
    
    def check_strategy_invalid(self, signals: Dict) -> bool:
        """策略失效条件"""
        anomaly = signals.get('anomaly', {})
        volume = signals.get('volume', {})
        
        # 假突破（新高但缩量）
        if anomaly.get('new_high') and volume.get('volume_ratio', 1) < 1:
            print("突破策略：假突破，策略失效")
            return True
        
        return False


class MomentumStrategy:
    """动量策略"""
    
    def __init__(self, name: str = '动量策略 v1', config: Dict = None):
        self.name = name
        self.config = config or {}
        self.position = 0
        self.entry_price = 0
    
    def check_entry_condition(self, signals: Dict) -> bool:
        """
        入场条件：
        1. 趋势强劲 (trend_score >= 2)
        2. 放量上涨 (volume_signal = '放量上涨')
        3. 无极端波动 (vol_signal != '高风险')
        """
        trend = signals.get('trend', {})
        volume = signals.get('volume', {})
        volatility = signals.get('volatility', {})
        
        # 条件 1: 趋势强劲
        if trend.get('trend_score', 0) < 2:
            return False
        
        # 条件 2: 放量上涨
        if volume.get('volume_signal') != '放量上涨':
            return False
        
        # 条件 3: 无极端波动
        if volatility.get('vol_signal') == '高风险':
            return False
        
        print("动量策略：满足入场条件")
        return True
    
    def check_exit_condition(self, signals: Dict, current_price: float) -> bool:
        """
        出场条件：
        1. 趋势减弱 (trend_score <= 0)
        2. 缩量 (volume_signal = '缩量')
        """
        trend = signals.get('trend', {})
        volume = signals.get('volume', {})
        
        # 条件 1: 趋势减弱
        if trend.get('trend_score', 0) <= 0:
            print("动量策略：趋势减弱，出场")
            return True
        
        # 条件 2: 缩量
        if volume.get('volume_signal') == '缩量':
            print("动量策略：缩量，出场")
            return True
        
        return False
    
    def check_strategy_invalid(self, signals: Dict) -> bool:
        """策略失效条件"""
        trend = signals.get('trend', {})
        volatility = signals.get('volatility', {})
        
        # 趋势反转
        if trend.get('trend_score', 0) <= -2:
            print("动量策略：趋势反转，策略失效")
            return True
        
        # 高波动
        if volatility.get('vol_signal') == '高风险':
            print("动量策略：高波动，策略失效")
            return True
        
        return False


class ReversalStrategy:
    """反转策略"""
    
    def __init__(self, name: str = '反转策略 v1', config: Dict = None):
        self.name = name
        self.config = config or {}
        self.position = 0
        self.entry_price = 0
    
    def check_entry_condition(self, signals: Dict) -> bool:
        """
        入场条件：
        1. 极端下跌 (z_score < -3)
        2. 超卖 (bb_position < 0.05)
        3. 出现缺口 (gap_down)
        """
        anomaly = signals.get('anomaly', {})
        volatility = signals.get('volatility', {})
        
        # 条件 1: 极端下跌
        if anomaly.get('return_zscore', 0) > -3:
            return False
        
        # 条件 2: 超卖
        if volatility.get('bb_position', 1) > 0.05:
            return False
        
        # 条件 3: 出现缺口（可选）
        # if not anomaly.get('gap_down', False):
        #     return False
        
        print("反转策略：满足入场条件")
        return True
    
    def check_exit_condition(self, signals: Dict, current_price: float) -> bool:
        """
        出场条件：
        1. 反弹超过 5%
        2. 趋势转强 (trend_score >= 1)
        """
        trend = signals.get('trend', {})
        
        # 条件 1: 反弹超过 5%
        if self.position > 0 and current_price > self.entry_price * 1.05:
            print("反转策略：反弹获利，出场")
            return True
        
        # 条件 2: 趋势转强
        if trend.get('trend_score', 0) >= 1:
            print("反转策略：趋势转强，出场")
            return True
        
        return False
    
    def check_strategy_invalid(self, signals: Dict) -> bool:
        """策略失效条件"""
        trend = signals.get('trend', {})
        anomaly = signals.get('anomaly', {})
        
        # 强势下跌（不接飞刀）
        if trend.get('trend_score', 0) <= -3:
            print("反转策略：强势下跌，策略失效")
            return True
        
        # 极端下跌后继续创新低
        if anomaly.get('new_low'):
            print("反转策略：继续创新低，策略失效")
            return True
        
        return False


class MultiStrategyFactory:
    """多策略工厂"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.strategies = {}
    
    def create_strategy(self, strategy_type: str, name: str = None) -> Optional[object]:
        """
        创建策略
        
        Args:
            strategy_type: 策略类型
                - 'trend': 趋势跟踪
                - 'mean_reversion': 均值回归
                - 'breakout': 突破
                - 'momentum': 动量
                - 'reversal': 反转
            name: 策略名称
            
        Returns:
            策略实例
        """
        if name is None:
            name = f"{strategy_type}_v1"
        
        if strategy_type == 'trend':
            from .strategy_definition import TrendFollowingStrategy
            strategy = TrendFollowingStrategy(name, self.config)
        elif strategy_type == 'mean_reversion':
            strategy = MeanReversionStrategy(name, self.config)
        elif strategy_type == 'breakout':
            strategy = BreakoutStrategy(name, self.config)
        elif strategy_type == 'momentum':
            strategy = MomentumStrategy(name, self.config)
        elif strategy_type == 'reversal':
            strategy = ReversalStrategy(name, self.config)
        else:
            raise ValueError(f"未知策略类型：{strategy_type}")
        
        self.strategies[name] = strategy
        print(f"创建策略：{name} ({strategy_type})")
        return strategy
    
    def get_strategy(self, name: str) -> Optional[object]:
        """获取策略"""
        return self.strategies.get(name)
    
    def list_strategies(self) -> List[str]:
        """列出所有策略"""
        return list(self.strategies.keys())


# 测试
if __name__ == '__main__':
    # 创建策略工厂
    factory = MultiStrategyFactory()
    
    # 创建不同策略
    strategies = {
        'trend': '趋势跟踪 v1',
        'mean_reversion': '均值回归 v1',
        'breakout': '突破策略 v1',
        'momentum': '动量策略 v1',
        'reversal': '反转策略 v1'
    }
    
    print('=' * 70)
    print('多策略创建测试')
    print('=' * 70)
    print()
    
    for strategy_type, name in strategies.items():
        strategy = factory.create_strategy(strategy_type, name)
        print(f'[OK] 创建{name}')
    
    print()
    print(f'策略列表：{factory.list_strategies()}')
    print()
    
    # 测试信号
    test_signals = {
        'trend': {'trend_score': 2, 'golden_cross': True},
        'volatility': {'vol_signal': '正常', 'bb_position': 0.1},
        'volume': {'volume_signal': '放量上涨', 'volume_ratio': 2.0},
        'anomaly': {'new_high': True, 'return_zscore': -1}
    }
    
    print('=' * 70)
    print('策略入场条件测试')
    print('=' * 70)
    print()
    
    for name, strategy in factory.strategies.items():
        can_enter = strategy.check_entry_condition(test_signals)
        print(f'{name}: {"可以入场" if can_enter else "不满足条件"}')
