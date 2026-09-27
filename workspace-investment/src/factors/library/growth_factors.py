"""
成长因子库（5 个因子）

G01: 营收增长率
G02: 净利润增长率
G03: ROE 增长率
G04: 毛利率增长率
G05: 经营性现金流增长率
"""

import pandas as pd
import numpy as np
from factor_library.factor_base import FactorBase


class GrowthFactors:
    """成长因子集合类"""
    
    def __init__(self):
        """初始化成长因子"""
        self.factors = {
            "G01": self.Revenue_Growth(),
            "G02": self.Profit_Growth(),
            "G03": self.ROE_Growth(),
            "G04": self.Gross_Margin_Growth(),
            "G05": self.CashFlow_Growth(),
        }
    
    def get_factor(self, code: str):
        """获取指定因子"""
        return self.factors.get(code)
    
    def get_all_factors(self) -> dict:
        """获取所有因子"""
        return self.factors
    
    # ========== G01: 营收增长率 ==========
    class Revenue_Growth(FactorBase):
        def __init__(self):
            super().__init__("营收增长率", "G01", "growth")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算营收增长率 = (今年营收 - 去年营收) / 去年营收
            
            需要财务数据支持
            """
            if '营收增长率' in df.columns:
                return df['营收增长率']
            elif '今年营收' in df.columns and '去年营收' in df.columns:
                growth = (df['今年营收'] - df['去年营收']) / df['去年营收'] * 100
                return growth.fillna(0)
            else:
                return pd.Series([10.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            营收增长率归一化（越高越好）
            >50% 得 100 分，<0% 得 0 分
            """
            normalized = (values + 0) / 50 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['营收']
    
    # ========== G02: 净利润增长率 ==========
    class Profit_Growth(FactorBase):
        def __init__(self):
            super().__init__("净利润增长率", "G02", "growth")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算净利润增长率 = (今年利润 - 去年利润) / 去年利润
            
            需要财务数据支持
            """
            if '净利润增长率' in df.columns:
                return df['净利润增长率']
            elif '今年净利润' in df.columns and '去年净利润' in df.columns:
                growth = (df['今年净利润'] - df['去年净利润']) / df['去年净利润'] * 100
                return growth.fillna(0)
            else:
                return pd.Series([15.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            净利润增长率归一化（越高越好）
            >50% 得 100 分，<0% 得 0 分
            """
            normalized = (values + 0) / 50 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['净利润']
    
    # ========== G03: ROE 增长率 ==========
    class ROE_Growth(FactorBase):
        def __init__(self):
            super().__init__("ROE 增长率", "G03", "growth")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算 ROE 增长率 = ROE 变化率
            
            需要财务数据支持
            """
            if 'ROE' in df.columns:
                roe_growth = df['ROE'].pct_change() * 100
                return roe_growth.fillna(0)
            else:
                return pd.Series([5.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            ROE 增长率归一化（越高越好）
            >20% 得 100 分，<0% 得 0 分
            """
            normalized = (values + 0) / 20 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['ROE']
    
    # ========== G04: 毛利率增长率 ==========
    class Gross_Margin_Growth(FactorBase):
        def __init__(self):
            super().__init__("毛利率增长率", "G04", "growth")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算毛利率增长率 = 毛利率变化率
            
            需要财务数据支持
            """
            if '毛利率' in df.columns:
                margin_growth = df['毛利率'].pct_change() * 100
                return margin_growth.fillna(0)
            else:
                return pd.Series([3.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            毛利率增长率归一化（越高越好）
            >10% 得 100 分，<0% 得 0 分
            """
            normalized = (values + 0) / 10 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['毛利率']
    
    # ========== G05: 经营性现金流增长率 ==========
    class CashFlow_Growth(FactorBase):
        def __init__(self):
            super().__init__("经营性现金流增长率", "G05", "growth")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算经营性现金流增长率 = (今年现金流 - 去年现金流) / 去年现金流
            
            需要财务数据支持
            """
            if '现金流增长率' in df.columns:
                return df['现金流增长率']
            elif '今年现金流' in df.columns and '去年现金流' in df.columns:
                growth = (df['今年现金流'] - df['去年现金流']) / df['去年现金流'] * 100
                return growth.fillna(0)
            else:
                return pd.Series([10.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            现金流增长率归一化（越高越好）
            >30% 得 100 分，<0% 得 0 分
            """
            normalized = (values + 0) / 30 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['现金流']


# 快捷函数
def get_growth_factor(code: str):
    """获取成长因子"""
    gf = GrowthFactors()
    return gf.get_factor(code)


def calculate_all_growth(df: pd.DataFrame) -> dict:
    """计算所有成长因子"""
    gf = GrowthFactors()
    results = {}
    
    for code, factor in gf.get_all_factors().items():
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
            print(f"成长因子 {code} 计算失败：{e}")
    
    return results
