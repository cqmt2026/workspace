# -*- coding: utf-8 -*-
"""
简化版 ML 评分器
不依赖外部模块，只保留核心评分逻辑
"""

import pandas as pd
import numpy as np
from typing import Dict

class SimpleStockScorer:
    """简化版股票评分器"""
    
    def __init__(self):
        pass
    
    def score_stock(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        对股票评分
        
        Args:
            symbol: 股票代码
            df: 价格数据 (OHLCV)
            
        Returns:
            评分字典
        """
        # 技术面评分 (40%)
        technical_score = self._technical_score(df)
        
        # 动量评分 (30%)
        momentum_score = self._momentum_score(df)
        
        # 波动率评分 (20%)
        volatility_score = self._volatility_score(df)
        
        # 成交量评分 (10%)
        volume_score = self._volume_score(df)
        
        # 综合评分
        total_score = (
            technical_score * 0.4 +
            momentum_score * 0.3 +
            volatility_score * 0.2 +
            volume_score * 0.1
        )
        
        return {
            'symbol': symbol,
            'technical': round(technical_score, 2),
            'momentum': round(momentum_score, 2),
            'volatility': round(volatility_score, 2),
            'volume': round(volume_score, 2),
            'total': round(total_score, 2),
            'rating': self._get_rating(total_score)
        }
    
    def _technical_score(self, df: pd.DataFrame) -> float:
        """技术面评分 (0-100)"""
        score = 50  # 基础分
        
        # 均线系统
        ma20 = df['close'].rolling(window=20).mean().iloc[-1]
        ma60 = df['close'].rolling(window=60).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        if current_price > ma20 > ma60:
            score += 30  # 多头排列
        elif current_price > ma20:
            score += 20
        elif current_price > ma60:
            score += 10
        elif current_price < ma60 < ma20:
            score -= 30  # 空头排列
        elif current_price < ma20:
            score -= 20
        elif current_price < ma60:
            score -= 10
        
        return max(0, min(100, score))
    
    def _momentum_score(self, df: pd.DataFrame) -> float:
        """动量评分 (0-100)"""
        score = 50
        
        # 计算动量
        returns = df['close'].pct_change()
        mom_5d = returns.rolling(window=5).mean().iloc[-1]
        mom_20d = returns.rolling(window=20).mean().iloc[-1]
        
        if mom_5d > 0.05:
            score += 30
        elif mom_5d > 0.02:
            score += 20
        elif mom_5d > 0:
            score += 10
        elif mom_5d < -0.05:
            score -= 30
        elif mom_5d < -0.02:
            score -= 20
        elif mom_5d < 0:
            score -= 10
        
        # 20 日动量加分
        if mom_20d > 0.1:
            score += 20
        elif mom_20d > 0.05:
            score += 10
        
        return max(0, min(100, score))
    
    def _volatility_score(self, df: pd.DataFrame) -> float:
        """波动率评分 (0-100, 越低波动越好)"""
        returns = df['close'].pct_change()
        volatility = returns.std()
        
        # 波动率分级
        if volatility < 0.01:
            return 90  # 低波动
        elif volatility < 0.02:
            return 70  # 中低波动
        elif volatility < 0.03:
            return 50  # 中等波动
        elif volatility < 0.05:
            return 30  # 高波动
        else:
            return 10  # 极高波动
    
    def _volume_score(self, df: pd.DataFrame) -> float:
        """成交量评分 (0-100)"""
        score = 50
        
        # 量比
        volume_ma20 = df['volume'].rolling(window=20).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / volume_ma20 if volume_ma20 > 0 else 1
        
        # 量价配合
        price_change = df['close'].pct_change().iloc[-1]
        
        if volume_ratio > 2 and price_change > 0:
            score += 40  # 放量上涨
        elif volume_ratio > 1.5 and price_change > 0:
            score += 30
        elif volume_ratio > 1 and price_change > 0:
            score += 20
        elif volume_ratio > 2 and price_change < 0:
            score -= 30  # 放量下跌
        elif volume_ratio < 0.5:
            score -= 20  # 极度缩量
        
        return max(0, min(100, score))
    
    def _get_rating(self, score: float) -> str:
        """获取评级"""
        if score >= 80:
            return '强烈推荐'
        elif score >= 70:
            return '推荐'
        elif score >= 60:
            return '谨慎推荐'
        elif score >= 50:
            return '中性'
        elif score >= 40:
            return '谨慎'
        elif score >= 30:
            return '不推荐'
        else:
            return '强烈不推荐'


# 测试
if __name__ == '__main__':
    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=252, freq='D')
    dates = dates[dates.weekday < 5]
    
    np.random.seed(42)
    base_price = 10
    returns = np.random.normal(0.0005, 0.02, len(dates))
    close = base_price * (1 + returns).cumprod()
    
    df = pd.DataFrame({
        'open': close * (1 + np.random.uniform(-0.01, 0.01, len(close))),
        'high': close * (1 + np.random.uniform(0, 0.02, len(close))),
        'low': close * (1 - np.random.uniform(0, 0.02, len(close))),
        'close': close,
        'volume': np.random.uniform(1000000, 5000000, len(close))
    }, index=dates)
    
    # 测试评分
    scorer = SimpleStockScorer()
    score = scorer.score_stock('000001.SZ', df)
    
    print('=' * 70)
    print('简化版 ML 评分器测试')
    print('=' * 70)
    print()
    print(f'股票代码：{score["symbol"]}')
    print(f'综合评分：{score["total"]} ({score["rating"]})')
    print()
    print('各维度评分:')
    print(f'  技术面：{score["technical"]}')
    print(f'  动量：{score["momentum"]}')
    print(f'  波动率：{score["volatility"]}')
    print(f'  成交量：{score["volume"]}')
