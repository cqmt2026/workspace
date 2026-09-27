"""因子存储 - 三维存储/预处理/快照"""
import os
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional, Any
from datetime import datetime


class FactorStore:
    """因子存储

    按日期-股票-因子名三维存储。
    支持去极值→中性化→标准化预处理。
    """

    def __init__(self, config=None):
        self._config = config
        self._store_dir = self._get_store_dir()
        os.makedirs(self._store_dir, exist_ok=True)
        self._cache: Dict[str, pd.DataFrame] = {}

    def save_factor(self, date: str, code: str, factor_name: str, value: float):
        """保存单个因子值"""
        key = f"{factor_name}_{date[:7]}"  # 按月分组
        if key not in self._cache:
            self._cache[key] = pd.DataFrame(columns=['date', 'code', 'factor_name', 'value'])
        self._cache[key] = pd.concat([
            self._cache[key],
            pd.DataFrame([{'date': date, 'code': code, 'factor_name': factor_name, 'value': value}])
        ], ignore_index=True)

    def save_factors_batch(self, df: pd.DataFrame):
        """批量保存因子

        Args:
            df: columns=['date', 'code', 'factor_name', 'value']
        """
        if df is None or df.empty:
            return

        # 按月分组存储
        df['month'] = df['date'].str[:7]
        for month, group in df.groupby('month'):
            key = f"factors_{month}"
            path = os.path.join(self._store_dir, f"{key}.parquet")
            group.drop('month', axis=1).to_parquet(path, index=False)

    def get_factor(self, code: str, factor_name: str, date: str) -> Optional[float]:
        """获取单个因子值"""
        month = date[:7]
        key = f"factors_{month}"
        path = os.path.join(self._store_dir, f"{key}.parquet")

        if not os.path.exists(path):
            return None

        try:
            df = pd.read_parquet(path)
            row = df[(df['code'] == code) & (df['factor_name'] == factor_name) & (df['date'] == date)]
            if not row.empty:
                return row.iloc[0]['value']
        except Exception:
            pass
        return None

    def get_factors(self, codes: List[str], factor_names: List[str],
                    date: str) -> pd.DataFrame:
        """批量获取因子"""
        month = date[:7]
        key = f"factors_{month}"
        path = os.path.join(self._store_dir, f"{key}.parquet")

        if not os.path.exists(path):
            return pd.DataFrame()

        try:
            df = pd.read_parquet(path)
            return df[(df['code'].isin(codes)) &
                      (df['factor_name'].isin(factor_names)) &
                      (df['date'] == date)]
        except Exception:
            return pd.DataFrame()

    def preprocess(self, series: pd.Series, method: str = 'zscore') -> pd.Series:
        """因子预处理

        Args:
            series: 因子值序列
            method: 预处理方法
                - 'winsorize': 去极值（百分位截断）
                - 'zscore': 标准化
                - 'rank': 排名标准化

        Returns:
            预处理后的序列
        """
        if series is None or series.empty:
            return series

        if method == 'winsorize':
            # 去极值：1%和99%百分位截断
            lower = series.quantile(0.01)
            upper = series.quantile(0.99)
            return series.clip(lower, upper)

        elif method == 'zscore':
            # 标准化
            mean = series.mean()
            std = series.std()
            if std == 0:
                return series * 0
            return (series - mean) / std

        elif method == 'rank':
            # 排名标准化
            ranks = series.rank()
            return (ranks - 1) / (len(ranks) - 1) * 2 - 1

        return series

    def neutralize(self, series: pd.Series, market_value: pd.Series = None,
                   industry: pd.Series = None) -> pd.Series:
        """因子中性化

        顺序：先中性化，后标准化。
        中性化：回归去市值/行业影响，取残差。

        Args:
            series: 因子值
            market_value: 市值（用于市值中性化）
            industry: 行业（用于行业中性化）

        Returns:
            中性化后的因子值
        """
        if market_value is None and industry is None:
            return series

        data = pd.DataFrame({'factor': series})

        if market_value is not None:
            data['log_mv'] = np.log(market_value + 1)

        if industry is not None:
            # 行业虚拟变量
            data = pd.concat([data, pd.get_dummies(industry, prefix='ind')], axis=1)

        # 线性回归取残差
        from sklearn.linear_model import LinearRegression
        X = data.drop('factor', axis=1).fillna(0)
        y = data['factor'].fillna(0)

        if len(X) == 0 or len(y) == 0:
            return series

        model = LinearRegression()
        model.fit(X, y)
        residuals = y - model.predict(X)
        return pd.Series(residuals.values, index=series.index)

    def _get_store_dir(self) -> str:
        """获取存储目录"""
        if self._config:
            base = self._config.get('data.db_path', '')
            if base:
                return os.path.join(os.path.dirname(base), 'factors')
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'factors')