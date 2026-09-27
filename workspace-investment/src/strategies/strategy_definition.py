# -*- coding: utf-8 -*-
"""
策略定义层
真正的策略来自规则，而不是感觉
AI 帮助把模糊想法转化为明确条件
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging; logger = logging

class TradingStrategy:
    """交易策略基类"""
    
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.position = 0  # 当前仓位
        self.entry_price = 0  # 入场价格
        self.stop_loss = 0  # 止损价格
        self.take_profit = 0  # 止盈价格
    
    def check_entry_condition(self, signals: Dict) -> bool:
        """
        检查入场条件
        
        Args:
            signals: 信号字典（来自信号生成层）
            
        Returns:
            是否满足入场条件
        """
        raise NotImplementedError
    
    def check_exit_condition(self, signals: Dict, current_price: float) -> bool:
        """
        检查出场条件
        
        Args:
            signals: 信号字典
            current_price: 当前价格
            
        Returns:
            是否满足出场条件
        """
        raise NotImplementedError
    
    def check_stop_loss(self, current_price: float) -> bool:
        """检查止损条件"""
        if self.position > 0 and current_price <= self.stop_loss:
            print(f"触发止损：{current_price} <= {self.stop_loss}")
            return True
        return False
    
    def check_take_profit(self, current_price: float) -> bool:
        """检查止盈条件"""
        if self.position > 0 and current_price >= self.take_profit:
            print(f"触发止盈：{current_price} >= {self.take_profit}")
            return True
        return False
    
    def check_strategy_invalid(self, signals: Dict) -> bool:
        """
        检查策略失效条件
        什么环境下策略失效
        """
        raise NotImplementedError


class TrendFollowingStrategy(TradingStrategy):
    """趋势跟踪策略"""
    
    def check_entry_condition(self, signals: Dict) -> bool:
        """
        入场条件：
        1. 趋势评分 >= 2（上涨或强势上涨）
        2. 价格在 MA20 之上
        3. 成交量信号为"放量上涨"或"正常"
        4. 无极端波动率
        """
        trend = signals.get('trend', {})
        volume = signals.get('volume', {})
        volatility = signals.get('volatility', {})
        
        # 条件 1: 趋势评分 >= 2
        if trend.get('trend_score', 0) < 2:
            return False
        
        # 条件 2: 价格在 MA20 之上
        if not trend.get('above_ma20', False):
            return False
        
        # 条件 3: 成交量正常或放量上涨
        volume_signal = volume.get('volume_signal', '')
        if volume_signal not in ['放量上涨', '正常']:
            return False
        
        # 条件 4: 无极端波动率
        vol_signal = volatility.get('vol_signal', '')
        if vol_signal == '高风险':
            return False
        
        print("趋势跟踪策略：满足入场条件")
        return True
    
    def check_exit_condition(self, signals: Dict, current_price: float) -> bool:
        """
        出场条件：
        1. 趋势评分 <= -1（下跌或更差）
        2. 价格跌破 MA20
        """
        trend = signals.get('trend', {})
        
        # 条件 1: 趋势评分 <= -1
        if trend.get('trend_score', 0) <= -1:
            print("趋势跟踪策略：趋势转弱，出场")
            return True
        
        # 条件 2: 价格跌破 MA20
        if not trend.get('above_ma20', False) and self.position > 0:
            print("趋势跟踪策略：跌破 MA20，出场")
            return True
        
        return False
    
    def check_strategy_invalid(self, signals: Dict) -> bool:
        """
        策略失效条件：
        1. 波动率急剧上升（市场混乱）
        2. 成交量极度萎缩（流动性枯竭）
        """
        volatility = signals.get('volatility', {})
        volume = signals.get('volume', {})
        
        # 波动率急剧上升
        if volatility.get('vol_state') == '波动率急剧上升':
            print("趋势跟踪策略：波动率急剧上升，策略失效")
            return True
        
        # 成交量极度萎缩
        if volume.get('volume_ratio', 1) < 0.3:
            print("趋势跟踪策略：成交量极度萎缩，策略失效")
            return True
        
        return False


class MeanReversionStrategy(TradingStrategy):
    """均值回归策略"""
    
    def check_entry_condition(self, signals: Dict) -> bool:
        """
        入场条件：
        1. 价格在布林带下轨附近（bb_position < 0.2）
        2. 出现极端下跌（z_score < -2）
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
        1. 价格回归到布林带中轨以上（bb_position > 0.5）
        2. 趋势转强（trend_score >= 2）
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
        """
        策略失效条件：
        1. 强势单边趋势（trend_score >= 3 或 <= -3）
        2. 波动率压缩（可能突破）
        """
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


class StrategyFactory:
    """策略工厂"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.strategies = {}
    
    def create_strategy(self, strategy_type: str, name: str) -> TradingStrategy:
        """
        创建策略
        
        Args:
            strategy_type: 策略类型（trend/mean_reversion）
            name: 策略名称
            
        Returns:
            策略实例
        """
        if strategy_type == 'trend':
            strategy = TrendFollowingStrategy(name, self.config)
        elif strategy_type == 'mean_reversion':
            strategy = MeanReversionStrategy(name, self.config)
        else:
            raise ValueError(f"未知策略类型：{strategy_type}")
        
        self.strategies[name] = strategy
        print(f"创建策略：{name} ({strategy_type})")
        return strategy
    
    def get_strategy(self, name: str) -> Optional[TradingStrategy]:
        """获取策略"""
        return self.strategies.get(name)


# 测试
if __name__ == '__main__':
    # 创建策略工厂
    factory = StrategyFactory({})
    
    # 创建趋势跟踪策略
    trend_strategy = factory.create_strategy('trend', '趋势跟踪 v1')
    
    # 测试信号
    test_signals = {
        'trend': {
            'trend_score': 2,
            'above_ma20': True,
        },
        'volume': {
            'volume_signal': '放量上涨',
        },
        'volatility': {
            'vol_signal': '正常',
            'bb_position': 0.3,
        },
        'anomaly': {
            'return_zscore': 0,
        }
    }
    
    # 检查入场条件
    can_enter = trend_strategy.check_entry_condition(test_signals)
    print(f"入场条件：{can_enter}")
    
    # 检查策略失效
    is_invalid = trend_strategy.check_strategy_invalid(test_signals)
    print(f"策略失效：{is_invalid}")
