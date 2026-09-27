"""
因子计算器

综合计算多个因子的评分
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from .technical_factors import TechnicalFactors
from .moneyflow_factors import MoneyFlowFactors


class FactorCalculator:
    """因子计算器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化因子计算器
        
        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            config_path = Path(__file__).parent / "factor_config.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"警告：配置文件加载失败：{e}")
            # 使用默认配置
            self.config = {
                "version": "1.0.0",
                "categories": {}
            }
        
        # 初始化因子集合
        self.technical = TechnicalFactors()
        self.moneyflow = MoneyFlowFactors()
    
    def calculate_single_factor(self, df: pd.DataFrame, factor_code: str) -> float:
        """
        计算单个因子
        
        Args:
            df: 股票数据 DataFrame
            factor_code: 因子代码（如 T01, M01）
        
        Returns:
            归一化后的因子值（0-100）
        """
        # 根据代码前缀选择因子类别
        if factor_code.startswith('T'):
            factor = self.technical.get_factor(factor_code)
        elif factor_code.startswith('M'):
            factor = self.moneyflow.get_factor(factor_code)
        else:
            raise ValueError(f"未知因子代码：{factor_code}")
        
        if factor is None:
            raise ValueError(f"因子不存在：{factor_code}")
        
        # 计算并归一化
        raw_value = factor.calculate(df)
        normalized_value = factor.normalize(raw_value)
        
        return normalized_value.iloc[-1] if len(normalized_value) > 0 else 50.0
    
    def calculate_composite_score(self, df: pd.DataFrame, 
                                   factors: list = None, 
                                   weights: list = None) -> float:
        """
        计算综合评分
        
        Args:
            df: 股票数据 DataFrame
            factors: 因子代码列表（如 ['T01', 'T04', 'M01']）
            weights: 权重列表（如 [0.3, 0.2, 0.25]）
        
        Returns:
            综合评分（0-100）
        """
        # 默认因子（当前 V13.3 使用的）
        if factors is None:
            factors = ['T06', 'T04', 'M04']  # 涨跌幅、成交量比、成交额
        
        # 默认权重
        if weights is None:
            weights = [0.5, 0.3, 0.2]
        
        # 计算各因子得分
        scores = []
        for factor_code in factors:
            try:
                score = self.calculate_single_factor(df, factor_code)
                scores.append(score)
            except Exception as e:
                print(f"因子 {factor_code} 计算失败：{e}")
                scores.append(50.0)  # 默认中位数
        
        # 加权平均
        weights = np.array(weights)
        weights = weights / weights.sum()  # 归一化权重
        scores = np.array(scores)
        
        composite_score = np.dot(scores, weights)
        
        return composite_score
    
    def calculate_all_factors(self, df: pd.DataFrame) -> dict:
        """
        计算所有可用因子
        
        Args:
            df: 股票数据 DataFrame
        
        Returns:
            所有因子结果字典
        """
        results = {}
        
        # 技术因子
        tech_results = self.technical.get_all_factors()
        for code, factor in tech_results.items():
            try:
                if factor.validate(df):
                    raw = factor.calculate(df).iloc[-1]
                    normalized = factor.normalize(factor.calculate(df)).iloc[-1]
                    results[code] = {
                        'raw': raw,
                        'normalized': normalized,
                        'info': factor.get_info()
                    }
            except Exception as e:
                print(f"技术因子 {code} 计算失败：{e}")
        
        # 资金因子
        mf_results = self.moneyflow.get_all_factors()
        for code, factor in mf_results.items():
            try:
                if factor.validate(df):
                    raw = factor.calculate(df).iloc[-1]
                    normalized = factor.normalize(factor.calculate(df)).iloc[-1]
                    results[code] = {
                        'raw': raw,
                        'normalized': normalized,
                        'info': factor.get_info()
                    }
            except Exception as e:
                print(f"资金因子 {code} 计算失败：{e}")
        
        return results
    
    def get_factor_rank(self, df: pd.DataFrame, factor_code: str) -> int:
        """
        获取因子排名
        
        Args:
            df: 股票数据 DataFrame
            factor_code: 因子代码
        
        Returns:
            排名（1 为最好）
        """
        score = self.calculate_single_factor(df, factor_code)
        
        # 计算该因子在所有股票中的百分位
        # 这里简化处理，实际需要全市场数据
        if score >= 80:
            return 1  # 前 20%
        elif score >= 60:
            return 2  # 前 40%
        elif score >= 40:
            return 3  # 中 40%
        elif score >= 20:
            return 4  # 后 40%
        else:
            return 5  # 后 20%
    
    def get_recommendation(self, composite_score: float) -> str:
        """
        根据综合评分给出建议
        
        Args:
            composite_score: 综合评分
        
        Returns:
            建议字符串
        """
        if composite_score >= 80:
            return "强烈买入"
        elif composite_score >= 70:
            return "买入"
        elif composite_score >= 60:
            return "增持"
        elif composite_score >= 50:
            return "持有"
        elif composite_score >= 40:
            return "减持"
        elif composite_score >= 30:
            return "卖出"
        else:
            return "强烈卖出"


# 快捷函数
def calculate(df: pd.DataFrame, factors: list = None, weights: list = None) -> float:
    """快捷计算综合评分"""
    calculator = FactorCalculator()
    return calculator.calculate_composite_score(df, factors, weights)


def get_all_factors(df: pd.DataFrame) -> dict:
    """快捷计算所有因子"""
    calculator = FactorCalculator()
    return calculator.calculate_all_factors(df)
