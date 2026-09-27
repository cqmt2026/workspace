"""训练器基类"""
from abc import ABC, abstractmethod
from typing import Tuple, Any, Dict, Optional
import numpy as np


class BaseTrainer(ABC):
    """训练器基类"""

    def __init__(self, params: Optional[Dict] = None):
        self.params = params or {}
        self.model = None
        self._is_trained = False

    @abstractmethod
    def train(self, X_train, y_train, X_val=None, y_val=None) -> Dict:
        """训练模型

        Args:
            X_train: 训练特征
            y_train: 训练标签
            X_val: 验证特征
            y_val: 验证标签

        Returns:
            训练记录 dict
        """
        pass

    @abstractmethod
    def predict(self, X) -> np.ndarray:
        """预测

        Args:
            X: 特征矩阵

        Returns:
            预测概率 (0~1)
        """
        pass

    @abstractmethod
    def save(self, path: str):
        """保存模型"""
        pass

    @abstractmethod
    def load(self, path: str):
        """加载模型"""
        pass

    def is_trained(self) -> bool:
        return self._is_trained