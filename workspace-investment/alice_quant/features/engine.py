"""特征工程引擎 - 核心重构

职责：
1. 因子注册中心管理（FactorRegistry）
2. 批量预计算因子，按日缓存
3. 回测时按日批量提供因子值
4. IC监控

数据流：
  DataHub.get_bars_batch() → FeatureEngine.compute() → 因子缓存 → 策略.get_factor()

不再依赖parquet按月存储，改为内存缓存+可选的DB持久化。
"""
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .registry import FactorRegistry
from .store import FactorStore
from .calculators import TechnicalFactors, MoneyFlowFactors, SectorFactors, PatternFactors, SentimentFactors, FundamentalFactors


class FeatureEngine:
    """特征工程引擎"""

    def __init__(self, config=None, datahub=None, logger=None):
        self._config = config
        self._datahub = datahub
        self._logger = logger
        self._registry = FactorRegistry()
        self._store = FactorStore(config)
        self._initialized = False

        # 内存缓存: {date: {code: {factor_name: value}}}
        self._factor_cache: Dict[str, Dict[str, Dict[str, float]]] = {}
        # 历史K线缓存: {code: DataFrame}
        self._kline_cache: Dict[str, pd.DataFrame] = {}
        # IC监控历史
        self._ic_history: List[dict] = []

    def initialize(self) -> bool:
        """初始化：注册内置因子"""
        self._register_builtin_factors()
        self._initialized = True
        self._log_info(f"特征引擎初始化完成", factors=self._registry.count())
        return True

    def precompute_all(self, codes: List[str], dates: List[str]):
        """预计算所有日期的所有因子

        回测启动时一次性计算，比逐日计算快10倍以上。
        一次批量拉取所有股票的所有历史K线，在内存中计算。

        Args:
            codes: 股票代码列表
            dates: 所有交易日期列表
        """
        if not codes or not dates:
            return

        max_window = self._get_max_window()
        start = self._calc_start_date(dates[0], max_window)
        end = dates[-1]

        self._log_info(f"预计算因子: {len(codes)}只, {len(dates)}天")

        # 一次批量获取所有股票的所有历史K线
        bars_batch = self._datahub.get_bars_batch(codes, start, end, '1d') if self._datahub else {}
        if not bars_batch:
            self._log_info("预计算失败: 无数据")
            return

        factors = self._registry.list_factors()
        factor_names = [f.name for f in factors]
        date_set = set(dates)

        # 按代码循环
        for code in codes:
            df = bars_batch.get(code)
            if df is None or df.empty:
                continue

            # 确保日期排序
            if 'date' in df.columns:
                df = df.sort_values('date')

            # 批量计算所有因子
            for factor_info in factors:
                calculator = self._registry.get_calculator(factor_info.name)
                if calculator is None:
                    continue

                try:
                    result = calculator(df)
                    if isinstance(result, pd.Series) and not result.empty:
                        for i, val in enumerate(result):
                            if pd.isna(val) or not np.isfinite(val):
                                continue
                            d = df.iloc[i].get('date', '')
                            if d in date_set:
                                if d not in self._factor_cache:
                                    self._factor_cache[d] = {}
                                if code not in self._factor_cache[d]:
                                    self._factor_cache[d][code] = {}
                                self._factor_cache[d][code][factor_info.name] = float(val)
                except Exception:
                    pass

        self._log_info(f"预计算完成: {len(self._factor_cache)}天")

    def compute_daily(self, codes: List[str], date: str):
        """计算当日所有因子的值

        为所有候选股票批量计算所有注册因子，存入内存缓存。
        一次批量拉取所有股票的历史K线，避免逐只查询。

        Args:
            codes: 股票代码列表
            date: 日期 (YYYY-MM-DD)
        """
        if not codes or not date:
            return

        # 已经缓存过当天的因子
        if date in self._factor_cache:
            return

        max_window = self._get_max_window()
        start = self._calc_start_date(date, max_window)

        # 一次批量获取所有股票的历史K线
        bars_batch = self._datahub.get_bars_batch(codes, start, date, '1d') if self._datahub else {}
        if not bars_batch:
            return

        # 计算每个因子
        day_factors: Dict[str, Dict[str, float]] = {}
        factors = self._registry.list_factors()

        # 按代码循环
        for code in codes:
            df = bars_batch.get(code)
            if df is None or df.empty:
                continue

            code_factors = {}
            for factor_info in factors:
                calculator = self._registry.get_calculator(factor_info.name)
                if calculator is None:
                    continue

                try:
                    result = calculator(df)
                    if isinstance(result, pd.Series) and not result.empty:
                        val = result.iloc[-1]
                        if not pd.isna(val) and np.isfinite(val):
                            code_factors[factor_info.name] = float(val)
                    elif isinstance(result, (int, float)):
                        code_factors[factor_info.name] = float(result)
                except Exception:
                    pass

            if code_factors:
                day_factors[code] = code_factors

        self._factor_cache[date] = day_factors

    def get_factor(self, code: str, factor_name: str, date: str) -> Optional[float]:
        """获取因子值

        优先从内存缓存读取，缓存未命中则从DataHub获取数据实时计算。

        Args:
            code: 股票代码
            factor_name: 因子名称
            date: 日期

        Returns:
            因子值 或 None
        """
        # 内存缓存
        if date in self._factor_cache and code in self._factor_cache[date]:
            val = self._factor_cache[date][code].get(factor_name)
            if val is not None:
                return val

        # 持久存储
        value = self._store.get_factor(code, factor_name, date)
        if value is not None:
            return value

        # 实时计算
        info = self._registry.get_info(factor_name)
        if info is None or not self._datahub:
            return None

        window = info.params.get('window', 20)
        start = self._calc_start_date(date, window * 2)
        bars = self._datahub.get_bars(code, start, date, '1d')
        if bars is None or bars.empty:
            return None

        calculator = self._registry.get_calculator(factor_name)
        if calculator is None:
            return None

        try:
            result = calculator(bars)
            if isinstance(result, pd.Series) and not result.empty:
                val = result.iloc[-1]
                if not pd.isna(val) and np.isfinite(val):
                    val = float(val)
                    self._store.save_factor(date, code, factor_name, val)
                    return val
        except Exception:
            pass
        return None

    def get_factors(self, codes: List[str], factor_names: List[str],
                    date: str) -> Dict[str, Dict[str, float]]:
        """批量获取因子

        Args:
            codes: 股票代码列表
            factor_names: 因子名称列表
            date: 日期

        Returns:
            {code: {factor_name: value}}
        """
        result: Dict[str, Dict[str, float]] = {}
        for code in codes:
            cf = {}
            for fname in factor_names:
                val = self.get_factor(code, fname, date)
                if val is not None:
                    cf[fname] = val
            if cf:
                result[code] = cf
        return result

    def compute_ic(self, date: str, factor_name: str,
                   forward_returns: Dict[str, float]) -> Optional[float]:
        """计算IC（信息系数）

        因子值与未来收益的Spearman相关系数。

        Args:
            date: 日期
            factor_name: 因子名称
            forward_returns: {code: 未来收益}

        Returns:
            IC值 或 None
        """
        if date not in self._factor_cache:
            return None

        factor_values = {}
        for code, factors in self._factor_cache[date].items():
            if factor_name in factors and code in forward_returns:
                factor_values[code] = factors[factor_name]

        if len(factor_values) < 10:
            return None

        codes_list = list(factor_values.keys())
        fv = [factor_values[c] for c in codes_list]
        fr = [forward_returns[c] for c in codes_list]

        from scipy.stats import spearmanr
        ic, p_value = spearmanr(fv, fr)

        record = {
            'date': date,
            'factor': factor_name,
            'ic': ic,
            'p_value': p_value,
            'n_stocks': len(codes_list),
        }
        self._ic_history.append(record)

        return ic

    def get_ic_summary(self, factor_name: Optional[str] = None,
                       window: int = 60) -> dict:
        """获取IC汇总

        Args:
            factor_name: 因子名称（不传则返回所有因子）
            window: 滚动窗口（天）

        Returns:
            {'mean_ic': float, 'ic_std': float, 'ic_ir': float, 'positive_ratio': float}
        """
        records = self._ic_history[-window:] if window > 0 else self._ic_history
        if factor_name:
            records = [r for r in records if r['factor'] == factor_name]

        if not records:
            return {'mean_ic': 0, 'ic_std': 0, 'ic_ir': 0, 'positive_ratio': 0}

        ics = [r['ic'] for r in records]
        mean_ic = np.mean(ics)
        ic_std = np.std(ics)
        ic_ir = mean_ic / ic_std if ic_std > 0 else 0
        positive_ratio = sum(1 for ic in ics if ic > 0) / len(ics)

        return {
            'mean_ic': mean_ic,
            'ic_std': ic_std,
            'ic_ir': ic_ir,
            'positive_ratio': positive_ratio,
            'n_samples': len(records),
        }

    def get_registry(self) -> FactorRegistry:
        return self._registry

    def list_active_factors(self) -> list:
        return self._registry.list_factors()

    def clear_cache(self):
        self._factor_cache.clear()
        self._kline_cache.clear()

    def _register_builtin_factors(self):
        """注册内置因子"""
        tf = TechnicalFactors()

        registrations = [
            # === 技术因子 (technical) ===
            ('ma_5', lambda df: tf.ma(df['close'], 5), {'window': 5}, '5日均线'),
            ('ma_10', lambda df: tf.ma(df['close'], 10), {'window': 10}, '10日均线'),
            ('ma_20', lambda df: tf.ma(df['close'], 20), {'window': 20}, '20日均线'),
            ('ma_60', lambda df: tf.ma(df['close'], 60), {'window': 60}, '60日均线'),
            ('rsi_14', lambda df: tf.rsi(df['close'], 14), {'window': 14}, 'RSI 14日'),
            ('vol_ratio', lambda df: tf.volume_ratio(df['volume'], 5), {'window': 5}, '量比'),
            ('pct_chg_1d', lambda df: tf.pct_change(df['close'], 1), {'periods': 1}, '日涨跌幅'),
            ('pct_chg_5d', lambda df: tf.pct_change(df['close'], 5), {'periods': 5}, '5日涨跌幅'),
            ('pct_chg_10d', lambda df: tf.pct_change(df['close'], 10), {'periods': 10}, '10日涨跌幅'),
            ('atr_14', lambda df: tf.atr(df['high'], df['low'], df['close'], 14), {'window': 14}, 'ATR 14日'),
            # === 资金流因子 (money_flow) ===
            ('flow_intensity', lambda df, c=None: MoneyFlowFactors.flow_intensity(c or 'sz.000001', df), {}, '5日资金强度', 'money_flow'),
            ('flow_persistence', lambda df, c=None: MoneyFlowFactors.flow_persistence(c or 'sz.000001', df), {}, '10日资金持续性', 'money_flow'),
            ('price_confirmation', lambda df, c=None: MoneyFlowFactors.price_confirmation(c or 'sz.000001', df), {}, '价量确认', 'money_flow'),
            ('impact_efficiency', lambda df, c=None: MoneyFlowFactors.impact_efficiency(c or 'sz.000001', df), {}, '冲击效率', 'money_flow'),
            ('smart_money_score', lambda df, c=None: MoneyFlowFactors.smart_money_score(c or 'sz.000001', df), {}, 'SmartMoney综合评分', 'money_flow'),
            # === 板块动量因子 (sector) ===
            ('sector_phase', lambda df, c=None: SectorFactors.sector_phase(c or 'sz.000001', df), {}, '板块周期阶段', 'sector'),
            ('sector_rps_5d', lambda df, c=None: SectorFactors.sector_rps_5d(c or 'sz.000001', df), {}, '板块5日RPS', 'sector'),
            ('sector_rps_10d', lambda df, c=None: SectorFactors.sector_rps_10d(c or 'sz.000001', df), {}, '板块10日RPS', 'sector'),
            ('relative_strength', lambda df, c=None: SectorFactors.relative_strength(c or 'sz.000001', df), {}, '个股相对板块强度', 'sector'),
            # === 形态因子 (pattern) ===
            ('pattern_strength', lambda df, c=None: PatternFactors.pattern_strength(c or 'sz.000001', df), {}, '强趋势延续', 'pattern'),
            ('pattern_reversal', lambda df, c=None: PatternFactors.pattern_reversal(c or 'sz.000001', df), {}, '底部反转', 'pattern'),
            ('pattern_wbottom', lambda df, c=None: PatternFactors.pattern_wbottom(c or 'sz.000001', df), {}, 'W底', 'pattern'),
            ('pattern_pullback', lambda df, c=None: PatternFactors.pattern_pullback(c or 'sz.000001', df), {}, '趋势回踩', 'pattern'),
            ('pattern_consolidation', lambda df, c=None: PatternFactors.pattern_consolidation(c or 'sz.000001', df), {}, '震荡整理', 'pattern'),
            ('pattern_mhead', lambda df, c=None: PatternFactors.pattern_mhead(c or 'sz.000001', df), {}, 'M头预警', 'pattern'),
            # === 情绪/ML因子 (sentiment) ===
            ('mx_sentiment', lambda df, c=None: SentimentFactors.mx_sentiment(c or 'sz.000001', df), {}, 'MXSearch舆情评分', 'sentiment'),
            ('ml_prob_lgb', lambda df, c=None: SentimentFactors.ml_prob_lgb(c or 'sz.000001', df), {}, 'LightGBM预测概率', 'ml'),
            ('ml_prob_mstnn', lambda df, c=None: SentimentFactors.ml_prob_mstnn(c or 'sz.000001', df), {}, 'MSTNN预测概率', 'ml'),
            # === 基本面因子 (fundamental) ===
            ('pe_ttm', lambda df, c=None: FundamentalFactors.pe_ttm(c or 'sz.000001', df), {}, '滚动市盈率', 'fundamental'),
            ('pb', lambda df, c=None: FundamentalFactors.pb(c or 'sz.000001', df), {}, '市净率', 'fundamental'),
            ('roe', lambda df, c=None: FundamentalFactors.roe(c or 'sz.000001', df), {}, '净资产收益率', 'fundamental'),
            ('roic', lambda df, c=None: FundamentalFactors.roic(c or 'sz.000001', df), {}, '投入资本回报率(近似)', 'fundamental'),
            ('earnings_yield', lambda df, c=None: FundamentalFactors.earnings_yield(c or 'sz.000001', df), {}, '收益率 1/PE', 'fundamental'),
            ('market_cap', lambda df, c=None: FundamentalFactors.market_cap(c or 'sz.000001', df), {}, '总市值(亿元)', 'fundamental'),
            ('profit_growth_q', lambda df, c=None: FundamentalFactors.profit_growth_q(c or 'sz.000001', df), {}, '净利润同比增长', 'fundamental'),
        ]
        for item in registrations:
            name, func, params, desc = item[0], item[1], item[2], item[3]
            category = item[4] if len(item) > 4 else 'technical'
            self._registry.register(
                name=name, category=category,
                calculator=func, description=desc, params=params
            )

    def _get_max_window(self) -> int:
        """获取所有因子中最大的窗口"""
        max_w = 60
        for f in self._registry.list_factors():
            w = f.params.get('window', 0)
            if w > max_w:
                max_w = w
        return max_w

    def _calc_start_date(self, end_date: str, lookback_days: int) -> str:
        end = datetime.strptime(end_date, '%Y-%m-%d')
        start = end - timedelta(days=lookback_days * 2)
        return start.strftime('%Y-%m-%d')

    def _log_info(self, msg: str, **kwargs):
        if self._logger:
            self._logger.info(msg, module='feature', **kwargs)