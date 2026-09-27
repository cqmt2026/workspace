# -*- coding: utf-8 -*-
"""
数据预处理器
做数据质量检查和清洗
"""
import numpy as np
import pandas as pd


class Preprocessor:
    """数据清洗和预处理"""

    @staticmethod
    def check_quality(df: pd.DataFrame, code: str) -> bool:
        """
        检查单只股票数据质量
        返回: True=可用, False=跳过
        """
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                return False

        # 检查缺失值
        if df[required_cols[1:]].isnull().any().any():
            return False

        # 检查价格异常（收盘价为0/负）
        if (df['close'] <= 0).any():
            return False

        # 检查高开低走（high < low）
        if (df['high'] < df['low']).any():
            return False

        # 检查成交量异常
        if (df['volume'] < 0).any():
            return False

        return True

    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        """清洗单只股票数据"""
        df = df.copy()
        df = df.sort_values('date').reset_index(drop=True)
        # 移除停牌日（成交量=0）的极端数据
        # 但保留停牌日（它们也是有效数据点）
        return df

    @staticmethod
    def align_data(data: dict) -> dict:
        """
        对齐所有股票的日期索引
        返回: 保留原始格式（逐股票dict）
        """
        # 当前设计：每只股票独立，日期对齐在样本构建时处理
        return data

    @staticmethod
    def report_stats(data: dict) -> dict:
        """生成数据统计报告"""
        stats = {
            'total_stocks': len(data),
            'total_rows': sum(len(df) for df in data.values()),
        }
        lengths = [len(df) for df in data.values()]
        stats['min_rows'] = min(lengths)
        stats['max_rows'] = max(lengths)
        stats['avg_rows'] = np.mean(lengths)
        return stats
