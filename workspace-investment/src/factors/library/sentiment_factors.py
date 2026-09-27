"""
情绪因子库（4 个因子）

S01: 换手率
S02: 涨停强度
S03: 量价配合
S04: 市场热度
"""

import pandas as pd
import numpy as np
from factor_library.factor_base import FactorBase


class SentimentFactors:
    """情绪因子集合类"""
    
    def __init__(self):
        """初始化情绪因子"""
        self.factors = {
            "S01": self.Turnover_Rate(),
            "S02": self.Limit_Up_Strength(),
            "S03": self.Volume_Price_Cooperation(),
            "S04": self.Market_Heat(),
        }
    
    def get_factor(self, code: str):
        """获取指定因子"""
        return self.factors.get(code)
    
    def get_all_factors(self) -> dict:
        """获取所有因子"""
        return self.factors
    
    # ========== S01: 换手率 ==========
    class Turnover_Rate(FactorBase):
        def __init__(self):
            super().__init__("换手率", "S01", "sentiment")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算换手率 = 成交量 / 流通股本
            
            需要流通股本数据
            """
            if '换手率' in df.columns:
                return df['换手率']
            elif '成交量' in df.columns and '流通股本' in df.columns:
                turnover = df['成交量'] / df['流通股本'] * 100
                return turnover.fillna(0)
            else:
                return pd.Series([3.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            换手率归一化（适中最好）
            3-10% 得高分，<1% 或>20% 得低分
            """
            # 使用二次函数，峰值在 6.5%
            normalized = 100 - abs(values - 6.5) / 10 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['成交量']
    
    # ========== S02: 涨停强度 ==========
    class Limit_Up_Strength(FactorBase):
        def __init__(self):
            super().__init__("涨停强度", "S02", "sentiment")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算涨停强度
            
            涨停 = 100 分
            涨幅>5% = 80 分
            涨幅>0% = 50 分
            跌幅 = 0-40 分
            """
            if '涨跌幅' in df.columns:
                def score(change):
                    if change >= 9.8:  # 涨停
                        return 100
                    elif change >= 5:
                        return 80
                    elif change >= 0:
                        return 50 + change / 5 * 30
                    else:
                        return max(0, 50 + change / 10 * 50)
                
                strength = df['涨跌幅'].apply(score)
                return strength
            else:
                return pd.Series([50.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """涨停强度已经是 0-100 分"""
            return values.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['涨跌幅']
    
    # ========== S03: 量价配合 ==========
    class Volume_Price_Cooperation(FactorBase):
        def __init__(self):
            super().__init__("量价配合", "S03", "sentiment")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算量价配合
            
            价涨量增 = 好（80-100 分）
            价跌量缩 = 中性（40-60 分）
            价涨量缩 = 警示（20-40 分）
            价跌量增 = 差（0-20 分）
            """
            if '涨跌幅' in df.columns and '成交量' in df.columns:
                # 计算量比
                vol_ma5 = df['成交量'].rolling(5).mean()
                vol_ratio = df['成交量'] / vol_ma5
                
                # 计算配合度
                price_change = df['涨跌幅']
                
                # 量价配合得分
                cooperation = price_change * vol_ratio
                return cooperation.fillna(0)
            else:
                return pd.Series([0.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            量价配合归一化
            >10 得 100 分，<-10 得 0 分
            """
            normalized = (values + 10) / 20 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['涨跌幅', '成交量']
    
    # ========== S04: 市场热度 ==========
    class Market_Heat(FactorBase):
        def __init__(self):
            super().__init__("市场热度", "S04", "sentiment")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算市场热度
            
            可以用板块涨停家数、成交量等综合判断
            简化：用成交量和涨跌幅综合计算
            """
            if '成交量' in df.columns and '涨跌幅' in df.columns:
                # 成交量得分
                vol_ma20 = df['成交量'].rolling(20).mean()
                vol_score = (df['成交量'] / vol_ma20 - 1) * 50 + 50
                
                # 涨跌幅得分
                price_score = df['涨跌幅'].clip(-10, 10) / 20 * 100 + 50
                
                # 综合热度
                heat = (vol_score + price_score) / 2
                return heat.fillna(50)
            else:
                return pd.Series([50.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """市场热度已经是 0-100 范围"""
            return values.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['成交量', '涨跌幅']


# 快捷函数
def get_sentiment_factor(code: str):
    """获取情绪因子"""
    sf = SentimentFactors()
    return sf.get_factor(code)


def calculate_all_sentiment(df: pd.DataFrame) -> dict:
    """计算所有情绪因子"""
    sf = SentimentFactors()
    results = {}
    
    for code, factor in sf.get_all_factors().items():
        try:
            if factor.validate(df):
                raw_value = factor.calculate(df)
                normalized_value = factor.normalize(raw_value)
                results[code] = {
                    'raw': raw_value.iloc[-1] if len(raw_value) > 0 else 0,
                    'normalized': normalized_value.iloc[-1] if len(normalized_value) > 0 else 0,
                    'factor': factor.get_info()
                }
        except Exception as e:
            print(f"情绪因子 {code} 计算失败：{e}")
    
    return results
