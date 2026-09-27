"""样本管理器 - 训练样本构建"""
import pandas as pd
import numpy as np
from typing import Optional, List, Tuple, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class SampleConfig:
    """样本配置"""
    positive_threshold: float = 0.03       # 正样本：未来N日涨幅>3%
    negative_threshold: float = -0.03      # 负样本：未来N日跌幅>3%
    forecast_horizon: int = 5              # 预测周期（交易日）
    train_ratio: float = 0.7               # 训练集比例
    val_ratio: float = 0.15                # 验证集比例
    test_ratio: float = 0.15               # 测试集比例
    balance_method: str = 'none'           # 平衡方法: none/oversample/undersample/smote
    min_samples: int = 100                 # 最小样本数


class SampleManager:
    """样本管理器"""

    def __init__(self, config: Optional[SampleConfig] = None):
        self._config = config or SampleConfig()

    def build_samples(self, data: pd.DataFrame,
                      feature_columns: List[str]) -> Tuple[pd.DataFrame, pd.Series]:
        """构建训练样本

        Args:
            data: 数据，必须包含日期和收益率列
                columns: ['date', 'code', 'return_N'] + feature_columns
            feature_columns: 特征列名列表

        Returns:
            (X, y): 特征矩阵和标签
        """
        df = data.copy()

        # 生成标签
        df['label'] = self._create_labels(df)

        # 过滤无效样本
        df = df.dropna(subset=['label'] + feature_columns)

        # 特征矩阵
        X = df[feature_columns].values
        y = df['label'].values

        # 样本平衡
        X, y = self._balance(X, y)

        return X, y

    def train_val_test_split(self, X, y, dates: List[str]) -> Tuple:
        """按时间顺序划分训练/验证/测试集

        Args:
            X: 特征矩阵
            y: 标签
            dates: 每个样本对应的日期

        Returns:
            (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        n = len(dates)
        train_end = int(n * self._config.train_ratio)
        val_end = int(n * (self._config.train_ratio + self._config.val_ratio))

        return (X[:train_end], X[train_end:val_end], X[val_end:],
                y[:train_end], y[train_end:val_end], y[val_end:])

    def _create_labels(self, df: pd.DataFrame) -> pd.Series:
        """创建标签

        基于未来N日收益率生成分类标签：
        1 = 正样本（涨幅>阈值）
        0 = 负样本（跌幅>阈值）
        -1 = 中性样本（忽略）
        """
        if 'return_N' not in df.columns:
            return pd.Series([-1] * len(df))

        labels = pd.Series(-1, index=df.index)
        labels[df['return_N'] >= self._config.positive_threshold] = 1
        labels[df['return_N'] <= self._config.negative_threshold] = 0
        return labels

    def _balance(self, X, y) -> Tuple:
        """样本平衡"""
        method = self._config.balance_method
        if method == 'none':
            return X, y

        # 统计各类别数量
        unique, counts = np.unique(y, return_counts=True)
        class_counts = dict(zip(unique, counts))

        if len(class_counts) < 2:
            return X, y

        if method == 'oversample':
            return self._oversample(X, y, class_counts)
        elif method == 'undersample':
            return self._undersample(X, y, class_counts)

        return X, y

    def _oversample(self, X, y, class_counts: dict):
        """过采样：复制少数类样本"""
        max_count = max(class_counts.values())
        indices = []
        for cls, count in class_counts.items():
            cls_idx = np.where(y == cls)[0]
            if count < max_count:
                # 随机复制
                repeat = max_count // count
                remainder = max_count % count
                indices.extend(np.repeat(cls_idx, repeat))
                if remainder > 0:
                    indices.extend(np.random.choice(cls_idx, remainder, replace=False))
            else:
                indices.extend(cls_idx)
        return X[np.array(indices)], y[np.array(indices)]

    def _undersample(self, X, y, class_counts: dict):
        """欠采样：随机删除多数类样本"""
        min_count = min(class_counts.values())
        indices = []
        for cls, count in class_counts.items():
            cls_idx = np.where(y == cls)[0]
            if count > min_count:
                indices.extend(np.random.choice(cls_idx, min_count, replace=False))
            else:
                indices.extend(cls_idx)
        return X[np.array(indices)], y[np.array(indices)]