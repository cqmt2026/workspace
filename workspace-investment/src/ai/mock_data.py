# -*- coding: utf-8 -*-
"""
Mock 数据模块
替代 realtime_data.TencentDataAPI
用于 advanced_scorer 的兼容层
"""

import pandas as pd
import numpy as np

class TencentDataAPI:
    """
    Mock 版腾讯财经 API
    提供与原版相同的接口，但不依赖真实 API
    """
    
    def __init__(self):
        pass
    
    def get_kline_data(self, code, period='d', count=120):
        """
        获取 K 线数据（Mock 版）
        
        Args:
            code: 股票代码
            period: 周期 ('d'=日线，'w'=周线)
            count: 数据条数
        
        Returns:
            DataFrame: OHLCV 数据
        """
        # 生成模拟数据
        dates = pd.date_range(end=pd.Timestamp.now(), periods=count, freq='D')
        dates = dates[dates.weekday < 5]  # 只保留工作日
        
        np.random.seed(hash(code) % 2**32 if code else 42)
        base_price = np.random.uniform(10, 100)
        returns = np.random.normal(0.0005, 0.02, len(dates))
        close = base_price * (1 + returns).cumprod()
        
        df = pd.DataFrame({
            'open': close * (1 + np.random.uniform(-0.01, 0.01, len(close))),
            'high': close * (1 + np.random.uniform(0, 0.02, len(close))),
            'low': close * (1 - np.random.uniform(0, 0.02, len(close))),
            'close': close,
            'volume': np.random.uniform(1000000, 5000000, len(close)),
            'amount': np.random.uniform(10000000, 50000000, len(close))
        }, index=dates)
        
        return df
    
    def get_stock_info(self, code):
        """
        获取股票基本信息（Mock 版）
        
        Args:
            code: 股票代码
        
        Returns:
            dict: 股票信息
        """
        return {
            'code': code,
            'name': 'Mock Stock',
            'sector': 'Mock Sector',
            'market_cap': np.random.uniform(100, 1000),
            'pe_ratio': np.random.uniform(10, 50),
            'pb_ratio': np.random.uniform(1, 5)
        }


# 测试
if __name__ == '__main__':
    api = TencentDataAPI()
    
    print('=' * 70)
    print('Mock 数据模块测试')
    print('=' * 70)
    print()
    
    # 测试 K 线数据
    df = api.get_kline_data('000001.SZ', period='d', count=60)
    print('[OK] 获取 K 线数据')
    print(f'     数据范围：{df.index.min().date()} 到 {df.index.max().date()}')
    print(f'     数据条数：{len(df)}')
    print(f'     列名：{list(df.columns)}')
    print()
    
    # 测试股票信息
    info = api.get_stock_info('000001.SZ')
    print('[OK] 获取股票信息')
    print(f'     代码：{info["code"]}')
    print(f'     名称：{info["name"]}')
    print(f'     板块：{info["sector"]}')
    print()
    
    print('=' * 70)
    print('Mock 数据模块测试通过!')
    print('=' * 70)
