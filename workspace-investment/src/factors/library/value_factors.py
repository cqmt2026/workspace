"""
价值因子库（5 个因子）

V01: 市盈率 PE
V02: 市净率 PB
V03: 市销率 PS
V04: 股息率
V05: 企业价值倍数 EV/EBITDA
"""

import pandas as pd
import numpy as np
from factor_library.factor_base import FactorBase


class ValueFactors:
    """价值因子集合类"""
    
    def __init__(self):
        """初始化价值因子"""
        self.factors = {
            "V01": self.PE_Ratio(),
            "V02": self.PB_Ratio(),
            "V03": self.PS_Ratio(),
            "V04": self.Dividend_Yield(),
            "V05": self.EV_EBITDA(),
        }
    
    def get_factor(self, code: str):
        """获取指定因子"""
        return self.factors.get(code)
    
    def get_all_factors(self) -> dict:
        """获取所有因子"""
        return self.factors
    
    # ========== V01: 市盈率 PE ==========
    class PE_Ratio(FactorBase):
        def __init__(self):
            super().__init__("市盈率", "V01", "value")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算市盈率 PE = 股价 / 每股收益
            
            需要财务数据支持
            """
            if '市盈率' in df.columns:
                return df['市盈率']
            elif '收盘' in df.columns and '每股收益' in df.columns:
                pe = df['收盘'] / df['每股收益']
                return pe.replace([np.inf, -np.inf], np.nan).fillna(100)
            else:
                return pd.Series([50.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            市盈率归一化（越低越好）
            PE<10 得 100 分，PE>50 得 0 分
            """
            # 反转：低 PE 得高分
            normalized = 100 - (values - 10) / 40 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['收盘']
    
    # ========== V02: 市净率 PB ==========
    class PB_Ratio(FactorBase):
        def __init__(self):
            super().__init__("市净率", "V02", "value")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算市净率 PB = 股价 / 每股净资产
            
            需要财务数据支持
            """
            if '市净率' in df.columns:
                return df['市净率']
            elif '收盘' in df.columns and '每股净资产' in df.columns:
                pb = df['收盘'] / df['每股净资产']
                return pb.replace([np.inf, -np.inf], np.nan).fillna(5)
            else:
                return pd.Series([3.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            市净率归一化（越低越好）
            PB<1 得 100 分，PB>10 得 0 分
            """
            normalized = 100 - (values - 1) / 9 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['收盘']
    
    # ========== V03: 市销率 PS ==========
    class PS_Ratio(FactorBase):
        def __init__(self):
            super().__init__("市销率", "V03", "value")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算市销率 PS = 市值 / 营收
            
            需要财务数据支持
            """
            if '市销率' in df.columns:
                return df['市销率']
            elif '市值' in df.columns and '营收' in df.columns:
                ps = df['市值'] / df['营收']
                return ps.replace([np.inf, -np.inf], np.nan).fillna(5)
            else:
                return pd.Series([5.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            市销率归一化（越低越好）
            PS<2 得 100 分，PS>20 得 0 分
            """
            normalized = 100 - (values - 2) / 18 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['市值']
    
    # ========== V04: 股息率 ==========
    class Dividend_Yield(FactorBase):
        def __init__(self):
            super().__init__("股息率", "V04", "value")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算股息率 = 分红 / 股价
            
            需要财务数据支持
            """
            if '股息率' in df.columns:
                return df['股息率'] * 100  # 转换为百分比
            elif '每股分红' in df.columns and '收盘' in df.columns:
                dividend_yield = df['每股分红'] / df['收盘'] * 100
                return dividend_yield.fillna(0)
            else:
                return pd.Series([2.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            股息率归一化（越高越好）
            股息率>5% 得 100 分，<1% 得 0 分
            """
            normalized = (values - 1) / 4 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['收盘']
    
    # ========== V05: 企业价值倍数 EV/EBITDA ==========
    class EV_EBITDA(FactorBase):
        def __init__(self):
            super().__init__("企业价值倍数", "V05", "value")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算 EV/EBITDA = 企业价值 / 税息折旧及摊销前利润
            
            需要财务数据支持
            """
            if 'EV_EBITDA' in df.columns:
                return df['EV_EBITDA']
            else:
                # 简化估算
                return pd.Series([10.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            EV/EBITDA 归一化（越低越好）
            <5 得 100 分，>20 得 0 分
            """
            normalized = 100 - (values - 5) / 15 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['收盘']


# 快捷函数
def get_value_factor(code: str):
    """获取价值因子"""
    vf = ValueFactors()
    return vf.get_factor(code)


def calculate_all_value(df: pd.DataFrame) -> dict:
    """计算所有价值因子"""
    vf = ValueFactors()
    results = {}
    
    for code, factor in vf.get_all_factors().items():
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
            print(f"价值因子 {code} 计算失败：{e}")
    
    return results
