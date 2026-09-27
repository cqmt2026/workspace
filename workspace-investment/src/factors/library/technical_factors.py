"""
技术因子库（6 个因子）

T01: 均线突破
T02: RSI
T03: MACD
T04: 成交量比
T05: 布林带位置
T06: 涨跌幅
"""

import pandas as pd
import numpy as np
from .factor_base import FactorBase


class TechnicalFactors:
    """技术因子集合类"""
    
    def __init__(self):
        """初始化技术因子"""
        self.factors = {
            "T01": self.MA_Breakthrough(),
            "T02": self.RSI(),
            "T03": self.MACD(),
            "T04": self.Volume_Ratio(),
            "T05": self.Bollinger_Position(),
            "T06": self.Price_Change(),
        }
    
    def get_factor(self, code: str):
        """获取指定因子"""
        return self.factors.get(code)
    
    def get_all_factors(self) -> dict:
        """获取所有因子"""
        return self.factors
    
    # ========== T01: 均线突破 ==========
    class MA_Breakthrough(FactorBase):
        def __init__(self):
            super().__init__("均线突破", "T01", "technical")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """计算均线突破因子"""
            if '收盘' not in df.columns or 'MA20' not in df.columns:
                # 计算 20 日均线
                df['MA20'] = df['收盘'].rolling(20).mean()
            
            # 股价/20 日均线
            ratio = df['收盘'] / df['MA20']
            return ratio
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """归一化到 0-100"""
            # 比率>1.1 得 100 分，<0.9 得 0 分
            normalized = (values - 0.9) / 0.2 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['收盘']
    
    # ========== T02: RSI ==========
    class RSI(FactorBase):
        def __init__(self):
            super().__init__("相对强弱指标", "T02", "technical")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """计算 RSI(14)"""
            delta = df['收盘'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """RSI 本身就是 0-100，但需要反转（低 RSI 好）"""
            # RSI<30 得 100 分（超卖），>70 得 0 分（超买）
            normalized = 100 - values
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['收盘']
    
    # ========== T03: MACD ==========
    class MACD(FactorBase):
        def __init__(self):
            super().__init__("平滑异同移动平均线", "T03", "technical")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """计算 MACD"""
            exp1 = df['收盘'].ewm(span=12, adjust=False).mean()
            exp2 = df['收盘'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            return macd
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """MACD 归一化"""
            # 使用分位数归一化
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            normalized = (values - q1) / (q3 - q1) * 50 + 50
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['收盘']
    
    # ========== T04: 成交量比 ==========
    class Volume_Ratio(FactorBase):
        def __init__(self):
            super().__init__("成交量比", "T04", "technical")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """计算成交量比（今日量/5 日均量）"""
            if '成交量' not in df.columns:
                return pd.Series([1.0] * len(df))
            
            vol_ma5 = df['成交量'].rolling(5).mean()
            volume_ratio = df['成交量'] / vol_ma5
            return volume_ratio.fillna(1.0)
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """归一化"""
            # 量比>2 得 100 分，<0.5 得 0 分
            normalized = (values - 0.5) / 1.5 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['成交量']
    
    # ========== T05: 布林带位置 ==========
    class Bollinger_Position(FactorBase):
        def __init__(self):
            super().__init__("布林带位置", "T05", "technical")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """计算布林带位置"""
            # 中轨 = 20 日均线
            middle = df['收盘'].rolling(20).mean()
            # 标准差
            std = df['收盘'].rolling(20).std()
            # 上轨和下轨
            upper = middle + 2 * std
            lower = middle - 2 * std
            
            # 位置 = (股价 - 下轨) / (上轨 - 下轨)
            position = (df['收盘'] - lower) / (upper - lower)
            return position.fillna(0.5)
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """布林带位置本身就是 0-1，转换到 0-100"""
            return values * 100
        
        def get_required_columns(self) -> list:
            return ['收盘']
    
    # ========== T06: 涨跌幅 ==========
    class Price_Change(FactorBase):
        def __init__(self):
            super().__init__("涨跌幅", "T06", "technical")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """计算涨跌幅"""
            if '涨跌幅' in df.columns:
                return df['涨跌幅']
            elif '收盘' in df.columns:
                return df['收盘'].pct_change() * 100
            else:
                return pd.Series([0.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """归一化"""
            # 涨跌幅>5% 得 100 分，<-5% 得 0 分
            normalized = (values + 5) / 10 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['收盘']


# 快捷函数
def get_technical_factor(code: str):
    """获取技术因子"""
    tech = TechnicalFactors()
    return tech.get_factor(code)


def calculate_all_technical(df: pd.DataFrame) -> dict:
    """计算所有技术因子"""
    tech = TechnicalFactors()
    results = {}
    
    for code, factor in tech.get_all_factors().items():
        if factor.validate(df):
            raw_value = factor.calculate(df)
            normalized_value = factor.normalize(raw_value)
            results[code] = {
                'raw': raw_value.iloc[-1] if len(raw_value) > 0 else 0,
                'normalized': normalized_value.iloc[-1] if len(normalized_value) > 0 else 0,
                'factor': factor.get_info()
            }
    
    return results
