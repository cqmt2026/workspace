"""
因子基类

所有因子类的父类，提供通用方法
"""

from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
import numpy as np


class FactorBase(ABC):
    """因子基类"""
    
    def __init__(self, name: str, code: str, category: str):
        """
        初始化因子
        
        Args:
            name: 因子名称
            code: 因子代码（如 T01, V01）
            category: 因子类别（technical, value, etc.）
        """
        self.name = name
        self.code = code
        self.category = category
        self.created_at = datetime.now()
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """
        计算因子值
        
        Args:
            df: 包含股票数据的 DataFrame
        
        Returns:
            因子值 Series
        """
        pass
    
    @abstractmethod
    def normalize(self, values: pd.Series) -> pd.Series:
        """
        归一化因子值（到 0-100 范围）
        
        Args:
            values: 原始因子值
        
        Returns:
            归一化后的因子值
        """
        pass
    
    def validate(self, df: pd.DataFrame) -> bool:
        """
        验证数据是否满足计算要求
        
        Args:
            df: 股票数据 DataFrame
        
        Returns:
            是否满足要求
        """
        required_columns = self.get_required_columns()
        return all(col in df.columns for col in required_columns)
    
    @abstractmethod
    def get_required_columns(self) -> list:
        """
        获取需要的数据列
        
        Returns:
            列名列表
        """
        pass
    
    def get_info(self) -> dict:
        """
        获取因子信息
        
        Returns:
            因子信息字典
        """
        return {
            "name": self.name,
            "code": self.code,
            "category": self.category,
            "created_at": str(self.created_at)
        }
