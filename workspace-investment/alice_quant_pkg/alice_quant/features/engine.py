"""Feature Engine - 特征工程主类"""
from typing import Optional, List, Dict, Any
import pandas as pd

from .registry import FactorRegistry
from .store import FactorStore
from .calculators import TechnicalFactors


class FeatureEngine:
    """特征工程引擎"""

    def __init__(self, config=None, datahub=None, logger=None):
        self._config = config
        self._datahub = datahub
        self._logger = logger
        self._registry = FactorRegistry()
        self._store = FactorStore(config)
        self._initialized = False

    def initialize(self) -> bool:
        """初始化：注册内置因子"""
        self._register_builtin_factors()
        self._initialized = True
        return True

    def _register_builtin_factors(self):
        """注册内置因子"""
        tf = TechnicalFactors()

        # 价量因子
        for name, func, params, desc in [
            ('ma_5', lambda df: tf.ma(df['close'], 5), {'window': 5}, '5日均线'),
            ('ma_10', lambda df: tf.ma(df['close'], 10), {'window': 10}, '10日均线'),
            ('ma_20', lambda df: tf.ma(df['close'], 20), {'window': 20}, '20日均线'),
            ('ma_60', lambda df: tf.ma(df['close'], 60), {'window': 60}, '60日均线'),
            ('rsi_14', lambda df: tf.rsi(df['close'], 14), {'window': 14}, 'RSI 14日'),
            ('vol_ratio', lambda df: tf.volume_ratio(df['volume'], 5), {'window': 5}, '量比'),
            ('atr_14', lambda df: tf.atr(df['high'], df['low'], df['close'], 14), {'window': 14}, 'ATR 14日'),
            ('pct_chg_1d', lambda df: tf.pct_change(df['close'], 1), {'periods': 1}, '日涨跌幅'),
            ('pct_chg_5d', lambda df: tf.pct_change(df['close'], 5), {'periods': 5}, '5日涨跌幅'),
            ('pct_chg_10d', lambda df: tf.pct_change(df['close'], 10), {'periods': 10}, '10日涨跌幅'),
        ]:
            self._registry.register(
                name=name, category='technical',
                calculator=func,
                description=desc, params=params
            )

    def get_factor(self, code: str, factor_name: str, date: str) -> Optional[float]:
        """获取因子值

        优先从存储读取，缓存未命中则从DataHub获取数据计算。
        """
        # 先查存储
        value = self._store.get_factor(code, factor_name, date)
        if value is not None:
            return value

        # 缓存未命中，尝试计算
        info = self._registry.get_info(factor_name)
        if info is None:
            return None

        # 从DataHub获取K线数据
        if self._datahub:
            # 根据因子参数计算所需的历史数据长度
            window = info.params.get('window', 20)
            lookback = window * 2  # 需要2倍窗口的数据
            start = self._calc_start_date(date, lookback)

            bars = self._datahub.get_bars(code, start, date, '1d')
            if bars is not None and not bars.empty:
                # 计算因子
                calculator = self._registry.get_calculator(factor_name)
                if calculator:
                    try:
                        result = calculator(bars)
                        if isinstance(result, pd.Series) and not result.empty:
                            value = result.iloc[-1]
                            if not pd.isna(value):
                                value = float(value)
                                self._store.save_factor(date, code, factor_name, value)
                                return value
                    except Exception as e:
                        if self._logger:
                            self._logger.debug(f"因子计算失败", factor=factor_name, code=code, error=str(e))

        return None

    def _calc_start_date(self, end_date: str, lookback_days: int) -> str:
        """计算开始日期"""
        from datetime import datetime, timedelta
        end = datetime.strptime(end_date, '%Y-%m-%d')
        start = end - timedelta(days=lookback_days * 2)  # 多留余量
        return start.strftime('%Y-%m-%d')

    def get_factors(self, codes: List[str], factor_names: List[str],
                    date: str) -> pd.DataFrame:
        """批量获取因子"""
        return self._store.get_factors(codes, factor_names, date)

    def prefetch(self, codes: List[str], factor_names: List[str],
                 start_date: str, end_date: str):
        """预加载因子

        批量计算并缓存因子值。
        """
        # TODO: 批量从DataHub获取数据并计算因子
        self._log_info(f"预加载因子: {len(codes)}只股票, {len(factor_names)}个因子")

    def get_registry(self) -> FactorRegistry:
        """获取因子注册中心"""
        return self._registry

    def list_active_factors(self) -> list:
        """列出当前有效的因子"""
        return self._registry.list_factors()

    def _log_info(self, msg: str):
        if self._logger:
            self._logger.info(msg, module='feature')