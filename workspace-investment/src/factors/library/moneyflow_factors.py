"""
资金因子库（5 个因子）

M01: 主力资金净流入
M02: 北向资金流入
M03: 融资买入额
M04: 成交额
M05: 资金流向强度
"""

import pandas as pd
import numpy as np
from .factor_base import FactorBase


class MoneyFlowFactors:
    """资金因子集合类"""
    
    def __init__(self):
        """初始化资金因子"""
        self.factors = {
            "M01": self.Main_Force_NetInflow(),
            "M02": self.North_Flow(),
            "M03": self.Margin_Buy(),
            "M04": self.Turnover_Amount(),
            "M05": self.Money_Flow_Strength(),
        }
    
    def get_factor(self, code: str):
        """获取指定因子"""
        return self.factors.get(code)
    
    def get_all_factors(self) -> dict:
        """获取所有因子"""
        return self.factors
    
    # ========== M01: 主力资金净流入 ==========
    class Main_Force_NetInflow(FactorBase):
        def __init__(self):
            super().__init__("主力资金净流入", "M01", "moneyflow")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算主力资金净流入
            
            简化算法：用大单估算
            主力净流入 = (收盘价 - 开盘价) × 成交量 / 100
            """
            if '收盘' in df.columns and '成交量' in df.columns:
                # 简化估算
                if '开盘' in df.columns:
                    net_inflow = (df['收盘'] - df['开盘']) * df['成交量'] / 100
                else:
                    net_inflow = df['收盘'].pct_change() * df['成交量'] / 100
                return net_inflow.fillna(0)
            else:
                return pd.Series([0.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """归一化"""
            # 使用分位数归一化
            if len(values) > 0:
                q1 = values.quantile(0.25)
                q3 = values.quantile(0.75)
                if q3 != q1:
                    normalized = (values - q1) / (q3 - q1) * 50 + 50
                    return normalized.clip(0, 100)
            return pd.Series([50.0] * len(values))
        
        def get_required_columns(self) -> list:
            return ['收盘', '成交量']
    
    # ========== M02: 北向资金流入 ==========
    class North_Flow(FactorBase):
        def __init__(self):
            super().__init__("北向资金流入", "M02", "moneyflow")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            北向资金流入
            
            注意：需要付费数据源
            简化：用成交额代理
            """
            if '成交额' in df.columns:
                # 简化估算：成交额大的股票更受外资关注
                return df['成交额']
            else:
                return pd.Series([0.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """归一化"""
            if len(values) > 0:
                q1 = values.quantile(0.25)
                q3 = values.quantile(0.75)
                if q3 != q1:
                    normalized = (values - q1) / (q3 - q1) * 50 + 50
                    return normalized.clip(0, 100)
            return pd.Series([50.0] * len(values))
        
        def get_required_columns(self) -> list:
            return ['成交额']
    
    # ========== M03: 融资买入额 ==========
    class Margin_Buy(FactorBase):
        def __init__(self):
            super().__init__("融资买入额", "M03", "moneyflow")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            融资买入额
            
            注意：需要额外数据源
            简化：用成交量代理
            """
            if '成交量' in df.columns:
                return df['成交量']
            else:
                return pd.Series([0.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """归一化"""
            if len(values) > 0:
                q1 = values.quantile(0.25)
                q3 = values.quantile(0.75)
                if q3 != q1:
                    normalized = (values - q1) / (q3 - q1) * 50 + 50
                    return normalized.clip(0, 100)
            return pd.Series([50.0] * len(values))
        
        def get_required_columns(self) -> list:
            return ['成交量']
    
    # ========== M04: 成交额 ==========
    class Turnover_Amount(FactorBase):
        def __init__(self):
            super().__init__("成交额", "M04", "moneyflow")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """计算成交额"""
            if '成交额' in df.columns:
                return df['成交额']
            elif '成交量' in df.columns and '收盘' in df.columns:
                return df['成交量'] * df['收盘']
            else:
                return pd.Series([0.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """归一化"""
            if len(values) > 0:
                q1 = values.quantile(0.25)
                q3 = values.quantile(0.75)
                if q3 != q1:
                    normalized = (values - q1) / (q3 - q1) * 50 + 50
                    return normalized.clip(0, 100)
            return pd.Series([50.0] * len(values))
        
        def get_required_columns(self) -> list:
            return ['成交量', '收盘']
    
    # ========== M05: 资金流向强度 ==========
    class Money_Flow_Strength(FactorBase):
        def __init__(self):
            super().__init__("资金流向强度", "M05", "moneyflow")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            资金流向强度 = 净流入 / 成交额
            
            反映资金流入的强度
            """
            if '收盘' in df.columns and '成交量' in df.columns:
                turnover = df['成交量'] * df['收盘']
                if '开盘' in df.columns:
                    net_inflow = (df['收盘'] - df['开盘']) * df['成交量']
                else:
                    net_inflow = df['收盘'].pct_change() * df['成交量']
                
                strength = net_inflow / (turnover + 1)
                return strength.fillna(0)
            else:
                return pd.Series([0.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """归一化"""
            # 强度 -0.1 到 0.1 映射到 0-100
            normalized = (values + 0.1) / 0.2 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['收盘', '成交量']


# 快捷函数
def get_moneyflow_factor(code: str):
    """获取资金因子"""
    mf = MoneyFlowFactors()
    return mf.get_factor(code)


def calculate_all_moneyflow(df: pd.DataFrame) -> dict:
    """计算所有资金因子"""
    mf = MoneyFlowFactors()
    results = {}
    
    for code, factor in mf.get_all_factors().items():
        if factor.validate(df):
            raw_value = factor.calculate(df)
            normalized_value = factor.normalize(raw_value)
            results[code] = {
                'raw': raw_value.iloc[-1] if len(raw_value) > 0 else 0,
                'normalized': normalized_value.iloc[-1] if len(normalized_value) > 0 else 0,
                'factor': factor.get_info()
            }
    
    return results
