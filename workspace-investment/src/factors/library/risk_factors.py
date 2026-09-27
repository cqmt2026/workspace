"""
风险因子库（5 个因子）

R01: 负债率
R02: 商誉占比
R03: 股东质押
R04: 连续亏损
R05: 审计意见
"""

import pandas as pd
import numpy as np
from factor_library.factor_base import FactorBase


class RiskFactors:
    """风险因子集合类"""
    
    def __init__(self):
        """初始化风险因子"""
        self.factors = {
            "R01": self.Debt_Ratio(),
            "R02": self.Goodwill_Ratio(),
            "R03": self.Share_Pledge(),
            "R04": self.Continuous_Loss(),
            "R05": self.Audit_Opinion(),
        }
    
    def get_factor(self, code: str):
        """获取指定因子"""
        return self.factors.get(code)
    
    def get_all_factors(self) -> dict:
        """获取所有因子"""
        return self.factors
    
    def check_risk_filter(self, df: pd.DataFrame, threshold: dict = None) -> bool:
        """
        风险过滤检查（一票否决）
        
        Args:
            df: 股票数据 DataFrame
            threshold: 风险阈值配置
        
        Returns:
            是否通过风险检查（True=安全，False=有风险）
        """
        if threshold is None:
            threshold = {
                'debt_ratio': 70,      # 负债率>70% 排除
                'goodwill_ratio': 30,  # 商誉占比>30% 排除
                'pledge_ratio': 50,    # 质押率>50% 排除
                'loss_years': 2,       # 连续亏损>2 年 排除
                'audit_opinion': '标准无保留'  # 非标准审计意见排除
            }
        
        # 检查负债率
        if '负债率' in df.columns:
            if df['负债率'].iloc[-1] > threshold['debt_ratio']:
                return False
        
        # 检查商誉占比
        if '商誉占比' in df.columns:
            if df['商誉占比'].iloc[-1] > threshold['goodwill_ratio']:
                return False
        
        # 检查质押率
        if '质押率' in df.columns:
            if df['质押率'].iloc[-1] > threshold['pledge_ratio']:
                return False
        
        # 检查连续亏损
        if '连续亏损年数' in df.columns:
            if df['连续亏损年数'].iloc[-1] > threshold['loss_years']:
                return False
        
        # 检查审计意见
        if '审计意见' in df.columns:
            if df['审计意见'].iloc[-1] != threshold['audit_opinion']:
                return False
        
        return True
    
    # ========== R01: 负债率 ==========
    class Debt_Ratio(FactorBase):
        def __init__(self):
            super().__init__("负债率", "R01", "risk")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算负债率 = 总负债 / 总资产
            
            需要财务数据支持
            """
            if '负债率' in df.columns:
                return df['负债率']
            elif '总负债' in df.columns and '总资产' in df.columns:
                debt_ratio = df['总负债'] / df['总资产'] * 100
                return debt_ratio.fillna(0)
            else:
                return pd.Series([50.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            负债率归一化（越低越好，但用于过滤）
            <30% 得 100 分，>70% 得 0 分
            """
            normalized = 100 - (values - 30) / 40 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['总负债', '总资产']
    
    # ========== R02: 商誉占比 ==========
    class Goodwill_Ratio(FactorBase):
        def __init__(self):
            super().__init__("商誉占比", "R02", "risk")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算商誉占比 = 商誉 / 净资产
            
            需要财务数据支持
            """
            if '商誉占比' in df.columns:
                return df['商誉占比']
            elif '商誉' in df.columns and '净资产' in df.columns:
                goodwill_ratio = df['商誉'] / df['净资产'] * 100
                return goodwill_ratio.fillna(0)
            else:
                return pd.Series([10.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            商誉占比归一化（越低越好）
            <10% 得 100 分，>30% 得 0 分
            """
            normalized = 100 - (values - 10) / 20 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['商誉', '净资产']
    
    # ========== R03: 股东质押 ==========
    class Share_Pledge(FactorBase):
        def __init__(self):
            super().__init__("股东质押", "R03", "risk")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算股东质押率 = 质押股数 / 持股总数
            
            需要股东数据支持
            """
            if '质押率' in df.columns:
                return df['质押率']
            elif '质押股数' in df.columns and '持股总数' in df.columns:
                pledge_ratio = df['质押股数'] / df['持股总数'] * 100
                return pledge_ratio.fillna(0)
            else:
                return pd.Series([20.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            质押率归一化（越低越好）
            <20% 得 100 分，>50% 得 0 分
            """
            normalized = 100 - (values - 20) / 30 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['质押股数', '持股总数']
    
    # ========== R04: 连续亏损 ==========
    class Continuous_Loss(FactorBase):
        def __init__(self):
            super().__init__("连续亏损", "R04", "risk")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            计算连续亏损年数
            
            需要财务数据支持
            """
            if '连续亏损年数' in df.columns:
                return df['连续亏损年数']
            elif '净利润' in df.columns:
                # 简化计算：统计连续负净利润的年数
                is_loss = df['净利润'] < 0
                # 这里简化处理
                loss_years = is_loss.sum()
                return pd.Series([loss_years] * len(df))
            else:
                return pd.Series([0.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """
            连续亏损归一化（越少越好）
            0 年得 100 分，>=3 年得 0 分
            """
            normalized = 100 - values / 3 * 100
            return normalized.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['净利润']
    
    # ========== R05: 审计意见 ==========
    class Audit_Opinion(FactorBase):
        def __init__(self):
            super().__init__("审计意见", "R05", "risk")
        
        def calculate(self, df: pd.DataFrame) -> pd.Series:
            """
            审计意见类型
            
            标准无保留 = 100 分
            带强调事项 = 60 分
            保留意见 = 30 分
            无法表示意见 = 0 分
            """
            if '审计意见' in df.columns:
                def score(opinion):
                    if '标准无保留' in str(opinion):
                        return 100
                    elif '强调事项' in str(opinion):
                        return 60
                    elif '保留意见' in str(opinion):
                        return 30
                    else:
                        return 0
                
                audit_score = df['审计意见'].apply(score)
                return audit_score
            else:
                return pd.Series([100.0] * len(df))
        
        def normalize(self, values: pd.Series) -> pd.Series:
            """审计意见已经是 0-100 分"""
            return values.clip(0, 100)
        
        def get_required_columns(self) -> list:
            return ['审计意见']


# 快捷函数
def get_risk_factor(code: str):
    """获取风险因子"""
    rf = RiskFactors()
    return rf.get_factor(code)


def calculate_all_risk(df: pd.DataFrame) -> dict:
    """计算所有风险因子"""
    rf = RiskFactors()
    results = {}
    
    for code, factor in rf.get_all_factors().items():
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
            print(f"风险因子 {code} 计算失败：{e}")
    
    return results


def risk_filter(df: pd.DataFrame) -> bool:
    """快捷风险过滤"""
    rf = RiskFactors()
    return rf.check_risk_filter(df)
