# -*- coding: utf-8 -*-
"""
信号生成层
AI 负责把数据压缩成可读结构：趋势、异常变化、波动率变化、流动性变化等
AI 的作用不是告诉你买什么，而是帮你看到哪些变量正在变化
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging; logger = logging

class SignalGenerator:
    """信号生成器"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def generate_trend_signal(self, df: pd.DataFrame, window: int = 20) -> Dict:
        """
        生成趋势信号
        
        Args:
            df: 价格数据（包含 close 列）
            window: 均线周期
            
        Returns:
            趋势信号字典
        """
        # 计算均线
        df['ma20'] = df['close'].rolling(window=window).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()
        
        # 当前趋势
        current_price = df['close'].iloc[-1]
        ma20 = df['ma20'].iloc[-1]
        ma60 = df['ma60'].iloc[-1]
        
        # 趋势判断
        if current_price > ma20 > ma60:
            trend = '强势上涨'
            trend_score = 3
        elif current_price > ma20:
            trend = '上涨'
            trend_score = 2
        elif current_price > ma60:
            trend = '震荡偏强'
            trend_score = 1
        elif current_price < ma60 < ma20:
            trend = '强势下跌'
            trend_score = -3
        elif current_price < ma20:
            trend = '下跌'
            trend_score = -2
        else:
            trend = '震荡偏弱'
            trend_score = -1
        
        # 均线斜率
        ma20_slope = (df['ma20'].iloc[-1] - df['ma20'].iloc[-5]) / df['ma20'].iloc[-5]
        
        return {
            'trend': trend,
            'trend_score': trend_score,
            'price': current_price,
            'ma20': ma20,
            'ma60': ma60,
            'ma20_slope': ma20_slope,
            'above_ma20': current_price > ma20,
            'above_ma60': current_price > ma60,
            'golden_cross': ma20 > ma60,  # 金叉
        }
    
    def generate_volatility_signal(self, df: pd.DataFrame, window: int = 20) -> Dict:
        """
        生成波动率信号
        
        Args:
            df: 价格数据
            window: 计算周期
            
        Returns:
            波动率信号字典
        """
        # 计算收益率
        returns = df['close'].pct_change()
        
        # 波动率
        volatility = returns.rolling(window=window).std()
        current_vol = volatility.iloc[-1]
        avg_vol = volatility.rolling(window=60).mean().iloc[-1]
        
        # 波动率变化
        vol_change = (current_vol - avg_vol) / avg_vol
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=window).mean()
        df['bb_std'] = df['close'].rolling(window=window).std()
        df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
        df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
        
        current_price = df['close'].iloc[-1]
        bb_position = (current_price - df['bb_lower'].iloc[-1]) / (df['bb_upper'].iloc[-1] - df['bb_lower'].iloc[-1])
        
        # 波动率状态判断
        if vol_change > 0.5:
            vol_state = '波动率急剧上升'
            vol_signal = '高风险'
        elif vol_change > 0.2:
            vol_state = '波动率上升'
            vol_signal = '风险增加'
        elif vol_change < -0.3:
            vol_state = '波动率压缩'
            vol_signal = '可能突破'
        else:
            vol_state = '正常波动'
            vol_signal = '正常'
        
        return {
            'volatility': current_vol,
            'vol_change': vol_change,
            'vol_state': vol_state,
            'vol_signal': vol_signal,
            'bb_position': bb_position,
            'near_upper': bb_position > 0.8,
            'near_lower': bb_position < 0.2,
        }
    
    def generate_volume_signal(self, df: pd.DataFrame, window: int = 20) -> Dict:
        """
        生成成交量信号
        
        Args:
            df: 价格数据（包含 volume 列）
            window: 计算周期
            
        Returns:
            成交量信号字典
        """
        if 'volume' not in df.columns:
            return {'error': '无成交量数据'}
        
        # 均量线
        avg_volume = df['volume'].rolling(window=window).mean()
        current_volume = df['volume'].iloc[-1]
        
        # 量比
        volume_ratio = current_volume / avg_volume.iloc[-1]
        
        # 量价关系
        price_change = df['close'].pct_change().iloc[-1]
        
        # 量价关系判断
        if volume_ratio > 2 and price_change > 0:
            volume_signal = '放量上涨'
            signal_strength = '强'
        elif volume_ratio > 2 and price_change < 0:
            volume_signal = '放量下跌'
            signal_strength = '强'
        elif volume_ratio < 0.5:
            volume_signal = '缩量'
            signal_strength = '弱'
        else:
            volume_signal = '正常'
            signal_strength = '中'
        
        return {
            'volume': current_volume,
            'avg_volume': avg_volume.iloc[-1],
            'volume_ratio': volume_ratio,
            'volume_signal': volume_signal,
            'signal_strength': signal_strength,
            'price_change': price_change,
        }
    
    def generate_anomaly_signal(self, df: pd.DataFrame, window: int = 60) -> Dict:
        """
        生成异常变化信号
        
        Args:
            df: 价格数据
            window: 历史周期
            
        Returns:
            异常信号字典
        """
        signals = {}
        
        # 价格异常（创 N 日新高/新低）
        high_n = df['high'].rolling(window=window).max()
        low_n = df['low'].rolling(window=window).min()
        
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]
        
        signals['new_high'] = current_high >= high_n.iloc[-1]
        signals['new_low'] = current_low <= low_n.iloc[-1]
        
        # 涨跌幅异常
        returns = df['close'].pct_change()
        mean_return = returns.rolling(window=window).mean()
        std_return = returns.rolling(window=window).std()
        
        current_return = returns.iloc[-1]
        z_score = (current_return - mean_return.iloc[-1]) / std_return.iloc[-1]
        
        signals['return_zscore'] = z_score
        signals['extreme_gain'] = z_score > 3  # 极端上涨
        signals['extreme_loss'] = z_score < -3  # 极端下跌
        
        # 缺口
        if len(df) > 1:
            gap = df['low'].iloc[-1] - df['high'].iloc[-2]
            signals['gap_up'] = gap > 0
            signals['gap_down'] = gap < 0
            signals['gap_size'] = gap / df['close'].iloc[-2]
        
        return signals
    
    def generate_all_signals(self, df: pd.DataFrame) -> Dict:
        """
        生成所有信号
        
        Args:
            df: 价格数据
            
        Returns:
            综合信号字典
        """
        # 至少需要 60 天数据
        if len(df) < 60:
            return {
                'trend': {'trend_score': 0, 'trend': '数据不足'},
                'volatility': {'vol_signal': '正常'},
                'volume': {'signal_strength': '中', 'price_change': 0},
                'anomaly': {},
                'composite_score': 0
            }
        
        signals = {}
        
        # 趋势信号
        signals['trend'] = self.generate_trend_signal(df)
        
        # 波动率信号
        signals['volatility'] = self.generate_volatility_signal(df)
        
        # 成交量信号
        signals['volume'] = self.generate_volume_signal(df)
        
        # 异常信号
        signals['anomaly'] = self.generate_anomaly_signal(df)
        
        # 综合评分
        trend_score = signals['trend']['trend_score']
        vol_score = -1 if signals['volatility']['vol_signal'] == '高风险' else 0
        volume_score = 1 if signals['volume'].get('signal_strength') == '强' and signals['volume'].get('price_change', 0) > 0 else 0
        
        signals['composite_score'] = trend_score + vol_score + volume_score
        
        return signals


# 测试
if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from loaders.data_loader import get_loader
    
    # 加载数据
    loader = get_loader('A')
    df = loader.load_market_data('000001.SZ', '2024-01-01', '2024-12-31')
    
    if not df.empty:
        # 生成信号
        generator = SignalGenerator({})
        signals = generator.generate_all_signals(df)
        
        print("\n=== 信号生成结果 ===")
        print(f"趋势：{signals['trend']['trend']} (评分：{signals['trend']['trend_score']})")
        print(f"波动率：{signals['volatility']['vol_state']} ({signals['volatility']['vol_signal']})")
        print(f"成交量：{signals['volume'].get('volume_signal', 'N/A')}")
        print(f"异常：新高={signals['anomaly']['new_high']}, 新低={signals['anomaly']['new_low']}")
        print(f"综合评分：{signals['composite_score']}")
