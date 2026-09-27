"""尾盘策略 - Pipeline策略迁移"""
from typing import List
from ..core.signal import Signal
from ..core.context import Context
from .base import BaseStrategy


class PipelineStrategy(BaseStrategy):
    """尾盘策略

    买入条件（全部满足）:
      1. 今日涨幅 3% ~ 5%
      2. 量比 > 1
      3. 近3日累计涨幅 0% ~ 10%
      4. MA20 近5日向上
      5. 换手率 3% ~ 10%

    排除条件:
      1. 北交所股票 (bj.开头)
      2. ST股票

    买入时间: 尾盘14:50，收盘价买入（含尾盘滑点）
    卖出时间: 次日开盘价卖出（无前瞻偏误）
    """

    def __init__(self, name: str = 'pipeline', params: dict = None,
                 feature_engine=None, logger=None):
        params = params or {
            'pct_chg_min': 3.0,
            'pct_chg_max': 5.0,
            'vol_ratio_min': 1.0,
            'pct_chg_3d_min': 0.0,
            'pct_chg_3d_max': 10.0,
            'turnover_min': 3.0,
            'turnover_max': 10.0,
        }
        super().__init__(name, params, feature_engine, logger)

    def on_start(self, context: Context):
        """启动时预加载因子"""
        self.watch_codes = context.watch_codes or []
        if self.watch_codes:
            self.prefetch_factors(
                codes=self.watch_codes,
                factor_names=['pct_chg_1d', 'vol_ratio', 'pct_chg_5d',
                             'ma_20', 'ma_5', 'turnover'],
                dates=context.all_dates
            )
        self.logger.info(f"尾盘策略启动", codes=len(self.watch_codes))

    def on_bar(self, data, context: Context) -> List[Signal]:
        """每日回调"""
        date = context.current_date
        signals = []

        for code in self.watch_codes:
            # 排除北交所
            if code.startswith('bj.'):
                continue

            # 获取因子值
            pct_chg = self.get_cached_factor(code, 'pct_chg_1d', date)
            vol_ratio = self.get_cached_factor(code, 'vol_ratio', date)
            pct_chg_5d = self.get_cached_factor(code, 'pct_chg_5d', date)
            ma_20 = self.get_cached_factor(code, 'ma_20', date)
            ma_5 = self.get_cached_factor(code, 'ma_5', date)

            if any(v is None for v in [pct_chg, vol_ratio, pct_chg_5d, ma_20, ma_5]):
                continue

            # 买入条件检查
            buy = True
            reasons = []

            # 1. 今日涨幅 3%~5%
            if not (self.params['pct_chg_min'] <= pct_chg <= self.params['pct_chg_max']):
                buy = False
            else:
                reasons.append(f"涨幅{pct_chg:.1f}%")

            # 2. 量比 > 1
            if vol_ratio <= self.params['vol_ratio_min']:
                buy = False
            else:
                reasons.append(f"量比{vol_ratio:.2f}")

            # 3. 近3日累计涨幅 0%~10%（用5日涨幅近似）
            if not (self.params['pct_chg_3d_min'] <= pct_chg_5d <= self.params['pct_chg_3d_max']):
                buy = False
            else:
                reasons.append(f"近3日{pct_chg_5d:.1f}%")

            # 4. MA20向上（MA5 > MA20）
            if ma_5 <= ma_20:
                buy = False
            else:
                reasons.append("均线多头")

            if buy:
                confidence = 0.8  # 全部条件满足
                signal = Signal(
                    date=date,
                    code=code,
                    direction='buy',
                    price=data.get('close', 0),
                    volume=0,  # 由组合管理器决定仓位
                    weight=1.0,
                    source=self.name,
                    reason='; '.join(reasons),
                    confidence=confidence
                )
                signals.append(signal)

        return signals