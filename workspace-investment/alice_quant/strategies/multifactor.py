"""多因子打分策略 - 综合评分选股

使用FeatureEngine的10个预置因子，加权打分。
评分维度：
  1. 动量（40%）：近5日涨幅 + RSI
  2. 趋势（30%）：均线多头排列 + 均线斜率
  3. 量能（20%）：量比 + ATR波动率
  4. 安全性（10%）：排除ST/北交所/涨幅过大

买入：综合评分前3的股票，尾盘买入
卖出：评分降到后50% 或 跌破MA20 或 持有超10天
"""
from typing import List, Dict, Any
import numpy as np
from ..core.signal import Signal
from ..core.context import Context
from .base import BaseStrategy


class MultiFactorStrategy(BaseStrategy):
    """多因子打分策略"""

    def __init__(self, name: str = 'multifactor', params: dict = None,
                 feature_engine=None, logger=None):
        params = params or {
            'score_momentum_weight': 0.40,
            'score_trend_weight': 0.30,
            'score_volume_weight': 0.20,
            'score_safety_weight': 0.10,
            'max_positions': 5,
            'max_hold_days': 10,
        }
        super().__init__(name, params, feature_engine, logger)

    def on_start(self, context: Context):
        self.watch_codes = context.watch_codes or []
        if self.logger:
            self.logger.info(f"多因子策略启动", codes=len(self.watch_codes))

    def on_bar(self, data, context: Context) -> List[Signal]:
        date = context.current_date
        account = context.account
        signals = []

        # 1. 计算每只股票的评分
        scores = []
        for code, bar in data.items():
            if code.startswith('bj.') or self._is_st(code):
                continue
            close = bar.get('close', 0)
            if close <= 0 or bar.get('volume', 0) <= 0:
                continue

            score = self._calc_score(code, date)
            if score > 0:
                scores.append((code, score, close))

        if not scores:
            return signals

        # 2. 卖出逻辑：检查现有持仓
        if account:
            for code, pos in list(account.positions.items()):
                # 检查是否应该卖出
                should_sell = False
                sell_reason = ''

                # 超时卖出
                if pos.days_held >= self.params['max_hold_days']:
                    should_sell = True
                    sell_reason = '持有超时'

                # 跌破MA20卖出
                ma20 = self._get_factor(code, 'ma_20', date)
                if ma20 is not None and close < ma20:
                    should_sell = True
                    sell_reason = '跌破MA20'

                # 评分降到后50%卖出
                if not should_sell:
                    code_scores = {c: s for c, s, _ in scores}
                    current_score = code_scores.get(code, 0)
                    if current_score > 0 and len(scores) > 2:
                        all_scores = sorted([s for _, s, _ in scores], reverse=True)
                        median = np.median(all_scores)
                        if current_score < median:
                            should_sell = True
                            sell_reason = '评分偏低'

                if should_sell:
                    signals.append(Signal(
                        date=date, code=code, direction='sell',
                        price=pos.current_price, volume=pos.volume,
                        source=self.name, reason=sell_reason, confidence=0.9
                    ))

        # 3. 买入逻辑：评分前3
        max_pos = self.params['max_positions']
        current_pos = len(account.positions) if account else 0
        remaining = max_pos - current_pos

        if remaining > 0:
            # 按评分排序
            scores.sort(key=lambda x: x[1], reverse=True)
            bought_codes = set()
            if account:
                bought_codes = set(account.positions.keys())

            for code, score, price in scores[:10]:
                if remaining <= 0:
                    break
                if code in bought_codes:
                    continue
                signals.append(Signal(
                    date=date, code=code, direction='buy',
                    price=price, volume=0, weight=score,
                    source=self.name,
                    reason=f'评分{score:.2f}',
                    confidence=min(0.5 + score * 0.1, 0.95)
                ))
                remaining -= 1

        return signals

    def _calc_score(self, code: str, date: str) -> float:
        """计算综合评分"""
        pct_chg_5d = self._get_factor(code, 'pct_chg_5d', date)
        rsi = self._get_factor(code, 'rsi_14', date)
        ma5 = self._get_factor(code, 'ma_5', date)
        ma20 = self._get_factor(code, 'ma_20', date)
        ma60 = self._get_factor(code, 'ma_60', date)
        vol_ratio = self._get_factor(code, 'vol_ratio', date)

        if any(v is None for v in [pct_chg_5d, rsi, ma5, ma20, ma60, vol_ratio]):
            return 0

        # 动量评分 (0~40)
        mom_score = 0
        if 0 < pct_chg_5d < 15:
            mom_score = (pct_chg_5d / 15) * 20  # 涨幅越接近15%越高
        if rsi > 50:
            mom_score += 20 * ((rsi - 50) / 50)  # RSI越高中高
        mom_score = min(mom_score, 40)

        # 趋势评分 (0~30)
        trend_score = 0
        if ma5 > ma20:
            trend_score += 15
        if ma20 > ma60:
            trend_score += 10
        if ma5 > ma60:
            trend_score += 5
        trend_score = min(trend_score, 30)

        # 量能评分 (0~20)
        vol_score = 0
        if vol_ratio > 1:
            vol_score = min(vol_ratio, 3) / 3 * 15  # 量比1~3线性评分
        vol_score = min(vol_score, 20)

        # 安全评分 (0~10)
        safety_score = 10
        if pct_chg_5d > 20:
            safety_score -= 5
        if rsi > 80:
            safety_score -= 5
        safety_score = max(safety_score, 0)

        total = mom_score + trend_score + vol_score + safety_score
        return total / 100.0  # 归一化到0~1

    def _get_factor(self, code: str, factor_name: str, date: str):
        if self.feature:
            return self.feature.get_factor(code, factor_name, date)
        return None

    def _is_st(self, code: str) -> bool:
        return code.startswith('st.') or 'st' in code.lower()