# -*- coding: utf-8 -*-
"""
数据加载器模块
负责自动收集市场数据、宏观数据、新闻、期权链、价格行为
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging; logger = logging

class DataLoader:
    """数据加载器基类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.data_dir = Path(__file__).parent.parent.parent / 'data'
        
    def load_market_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """加载市场数据（价格/成交量）"""
        raise NotImplementedError
    
    def load_macro_data(self, indicators: List[str]) -> pd.DataFrame:
        """加载宏观数据"""
        raise NotImplementedError
    
    def load_news(self, start_date: str, end_date: str) -> List[Dict]:
        """加载新闻数据"""
        raise NotImplementedError


class AKShareLoader(DataLoader):
    """AKShare 数据加载器（A 股数据）"""
    
    def load_market_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载 A 股市场数据
        
        Args:
            symbol: 股票代码（如：000001.SZ）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            
        Returns:
            DataFrame: 包含开盘/最高/最低/收盘/成交量数据
        """
        try:
            import akshare as ak
            
            # 获取日线数据
            df = ak.stock_zh_a_hist(
                symbol=symbol.split('.')[0],
                period="daily",
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust="qfq"  # 前复权
            )
            
            # 重命名列
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'amount'
            })
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            print(f"成功加载 {symbol} 数据，共{len(df)}条")
            return df
            
        except Exception as e:
            print(f"加载数据失败：{e}")
            return pd.DataFrame()
    
    def load_macro_data(self, indicators: List[str]) -> pd.DataFrame:
        """
        加载宏观数据
        
        Args:
            indicators: 指标列表（如：['CPI', 'PPI', 'M2', '社融']）
            
        Returns:
            DataFrame: 宏观数据
        """
        try:
            import akshare as ak
            
            macro_data = {}
            
            for indicator in indicators:
                if indicator == 'CPI':
                    df = ak.macro_china_cpi()
                elif indicator == 'PPI':
                    df = ak.macro_china_ppi()
                elif indicator == 'M2':
                    df = ak.macro_china_money_supply()
                elif indicator == '社融':
                    df = ak.macro_china_social_finance()
                else:
                    print(f"未知指标：{indicator}")
                    continue
                
                macro_data[indicator] = df
            
            return pd.DataFrame(macro_data)
            
        except Exception as e:
            print(f"加载宏观数据失败：{e}")
            return pd.DataFrame()


class YahooFinanceLoader(DataLoader):
    """Yahoo Finance 数据加载器（美股/港股数据）"""
    
    def load_market_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载美股/港股市场数据
        
        Args:
            symbol: 股票代码（如：AAPL, 0700.HK）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: OHLCV 数据
        """
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            print(f"成功加载 {symbol} 数据，共{len(df)}条")
            return df
            
        except Exception as e:
            print(f"加载数据失败：{e}")
            return pd.DataFrame()


def get_loader(market: str = 'A', config: Optional[Dict] = None) -> DataLoader:
    """
    获取数据加载器
    
    Args:
        market: 市场类型（A: A 股，US: 美股，HK: 港股）
        config: 配置字典
        
    Returns:
        DataLoader 实例
    """
    if config is None:
        config = {}
    
    if market == 'A':
        return AKShareLoader(config)
    elif market in ['US', 'HK']:
        return YahooFinanceLoader(config)
    else:
        raise ValueError(f"不支持的市场类型：{market}")


# 测试
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    # 测试 A 股数据加载
    loader = get_loader('A')
    df = loader.load_market_data('000001.SZ', '2024-01-01', '2024-12-31')
    
    if not df.empty:
        print(f"\n数据预览:")
        print(df.head())
        print(f"\n数据形状：{df.shape}")
        print(f"日期范围：{df.index.min()} 到 {df.index.max()}")
