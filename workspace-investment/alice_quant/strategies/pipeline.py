"""Pipeline策略 v2 — 多维度综合评分选股

基于35个因子的多维评分系统：

评分维度（满分100）：
  1. 动量趋势 (30分): 均线排列 + 板块周期 + 相对强度
  2. 量能确认 (20分): 量比 + 资金流强度 + 资金流持续性
  3. 价格形态 (15分): 形态信号 + 价量确认
  4. 基本面 (15分): PE/PB分位数 + 市值
  5. 情绪信号 (10分): MXSearch舆情 + ML预测
  6. 安全性 (10分): 排除ST/北交所/涨幅过高/拥挤度过高

市场状态过滤：
  - 大盘5日涨幅 > -3% → 正常交易（仓位上限5只）
  - 大盘5日涨幅 -3%~-5% → 减仓（仓位上限3只）
  - 大盘5日涨幅 < -5% → 停止交易

数据来源：
  - factors.db 持久化因子（优先）
  - FeatureEngine 实时计算（降级）
"""
from typing import List, Dict, Optional, Any
import numpy as np

from ..core.signal import Signal
from ..core.context import Context
from .base import BaseStrategy


class PipelineStrategy(BaseStrategy):
    """增强Pipeline策略 - 多维度评分"""

    def __init__(self, name: str = 'pipeline_v2', params: dict = None,
                 feature_engine=None, logger=None):
        defaults = {
            # 买入条件
            'pct_chg_min': 1.5,
            'pct_chg_max': 5.0,
            'vol_ratio_min': 0.8,
            'vol_ratio_bear_min': 1.2,
            # 仓位
            'max_positions_bull': 5,
            'max_positions_bear': 3,
            # 市场状态
            'benchmark_code': 'sz.000001',
            'bear_threshold': -3.0,
            'stop_threshold': -5.0,
            # 评分权重
            'weight_momentum': 0.30,
            'weight_volume': 0.20,
            'weight_pattern': 0.15,
            'weight_fundamental': 0.15,
            'weight_sentiment': 0.10,
            'weight_safety': 0.10,
            # 最小买入评分
            'min_score': 50,
        }
        merged = defaults.copy()
        if params:
            merged.update(params)
        super().__init__(name, merged, feature_engine, logger)

    def on_start(self, context: Context):
        self.watch_codes = context.watch_codes or []
        if self.logger:
            self.logger.info(f"Pipeline v2 启动", codes=len(self.watch_codes))

    def on_bar(self, data, context: Context) -> List[Signal]:
        date = context.current_date
        account = context.account
        signals = []

        # 1. 市场状态
        market_status = self._get_market_status(date)
        is_bear = market_status == 'bear'
        is_stop = market_status == 'stop'

        if is_stop:
            if self.logger:
                self.logger.info(f"市场状态: 停止交易", date=date)
            # 停止交易时，卖出所有持仓
            if account:
                for code, pos in list(account.positions.items()):
                    signals.append(Signal(
                        date=date, code=code, direction='sell',
                        price=pos.current_price, volume=pos.volume,
                        source=self.name, reason='市场停止交易', confidence=1.0
                    ))
            return signals

        max_pos = self.params['max_positions_bear'] if is_bear else self.params['max_positions_bull']
        vol_ratio_min = self.params['vol_ratio_bear_min'] if is_bear else self.params['vol_ratio_min']

        # 2. 筛选候选 + 评分
        candidates = self._score_candidates(data, date, vol_ratio_min)
        if not candidates:
            return signals

        # 3. 卖出逻辑
        if account:
            for code, pos in list(account.positions.items()):
                should_sell = False
                reason = ''

                # 跌破MA20
                ma20 = self._get_factor(code, 'ma_20', date)
                close = pos.current_price
                if ma20 is not None and close < ma20:
                    should_sell = True
                    reason = '跌破MA20'

                # 评分跌到后50%
                if not should_sell:
                    score_map = {c['code']: c['score'] for c in candidates}
                    current_score = score_map.get(code, 0)
                    if current_score > 0 and len(candidates) > 2:
                        all_scores = sorted([c['score'] for c in candidates], reverse=True)
                        median = np.median(all_scores)
                        if current_score < median:
                            should_sell = True
                            reason = f'评分{current_score:.0f}低于中位数{median:.0f}'

                # 形态预警
                if not should_sell:
                    mhead = self._get_factor(code, 'breakout_strength', date)
                    if mhead is not None and mhead > 0:
                        should_sell = True
                        reason = 'M头预警'

                if should_sell:
                    signals.append(Signal(
                        date=date, code=code, direction='sell',
                        price=pos.current_price, volume=pos.volume,
                        source=self.name, reason=reason, confidence=0.9
                    ))

        # 4. 买入逻辑
        current_pos = len(account.positions) if account else 0
        remaining = max_pos - current_pos

        if remaining > 0:
            candidates.sort(key=lambda x: x['score'], reverse=True)
            bought = set(account.positions.keys()) if account else set()

            for c in candidates[:10]:
                if remaining <= 0:
                    break
                if c['code'] in bought:
                    continue

                signals.append(Signal(
                    date=date, code=c['code'], direction='buy',
                    price=c['price'], volume=0, weight=c['score'] / 100.0,
                    source=self.name,
                    reason=f'评分{c["score"]:.0f} | {c["summary"]}',
                    confidence=min(0.5 + c['score'] * 0.005, 0.95)
                ))
                remaining -= 1

        return signals

    def _score_candidates(self, data: Dict[str, Dict], date: str,
                           vol_ratio_min: float) -> List[dict]:
        """评分所有候选股

        返回: [{'code': str, 'score': float, 'price': float, 'summary': str}, ...]
        """
        results = []
        for code, bar in data.items():
            if code.startswith('bj.') or self._is_st(code):
                continue

            close = bar.get('close', 0)
            if close <= 0 or bar.get('volume', 0) <= 0:
                continue

            score = self._calc_composite_score(code, date)
            if score is None or score < self.params['min_score']:
                continue

            summary = self._make_summary(code, date)
            results.append({
                'code': code, 'score': score,
                'price': close, 'summary': summary,
            })

        return results

    def generate_signals(self, date: str, codes: list = None) -> list:
        """生成实盘信号（独立入口，不依赖回测引擎）

        Args:
            date: 日期
            codes: 候选股列表，None则从DB获取全市场

        Returns:
            [{'code', 'score', 'price', 'summary'}, ...]
        """
        if not codes:
            import sqlite3
            conn = sqlite3.connect(r'F:\market_data.db')
            rows = conn.execute(
                "SELECT code FROM daily_k WHERE date=? "
                "AND code NOT LIKE 'bj.%%' AND code NOT LIKE 'sh.8%%' "
                "AND code NOT LIKE 'sh.9%%' AND close>0 AND volume>0",
                (date,)
            ).fetchall()
            conn.close()
            codes = [r[0] for r in rows]

        # 构造 data 字典
        from scripts.data_api import DataAPI
        data = {}
        for code in codes:
            klines = DataAPI.get_kline(code, days=1, end_date=date)
            if klines:
                k = klines[-1]
                data[code] = {
                    'close': k['close'],
                    'volume': k['volume'],
                    'high': k.get('high', k['close']),
                    'low': k.get('low', k['close']),
                    'amount': k.get('amount', 0),
                }

        results = self._score_candidates(data, date, self.params.get('vol_ratio_min', 1.0))
        results.sort(key=lambda x: -x['score'])
        return results

    def _calc_composite_score(self, code: str, date: str) -> Optional[float]:
        """计算综合评分

        返回: 0~100 分，None表示排除
        """
        # === 1. 安全过滤（硬性排除） ===
        pct_chg = self._get_factor(code, 'pct_chg_5d', date)
        if pct_chg is None:
            return None
        if pct_chg < self.params['pct_chg_min'] or pct_chg > self.params['pct_chg_max']:
            return None

        vol_ratio = self._get_factor(code, 'vol_ratio', date)
        if vol_ratio is None or vol_ratio <= 0.5:
            return None

        # === 2. 动量趋势评分 (0~30) ===
        momentum_score = 0.0

        # 均线排列 (15分)
        ma5 = self._get_factor(code, 'ma_5', date)
        ma20 = self._get_factor(code, 'ma_20', date)
        ma60 = self._get_factor(code, 'ma_60', date)
        if ma5 is not None and ma20 is not None:
            if ma5 > ma20:
                momentum_score += 8
                if ma60 is not None and ma20 > ma60:
                    momentum_score += 7  # 完美多头排列

        # 板块周期 (10分)
        sector_phase = self._get_factor(code, 'sector_phase', date)
        if sector_phase is not None:
            # sector_phase范围: -5~+8, 映射到0~10
            momentum_score += max(0, min(10, (sector_phase + 5) * 10 / 13))

        # 相对强度 (5分)
        rel_strength = self._get_factor(code, 'relative_strength', date)
        if rel_strength is not None:
            momentum_score += max(0, min(5, rel_strength / 2))

        momentum_score = min(momentum_score, 30)

        # === 3. 量能确认评分 (0~20) ===
        volume_score = 0.0

        # 量比 (8分)
        if vol_ratio > 1:
            volume_score += min(8, vol_ratio * 3)

        # 资金流强度 (7分)
        flow_intensity = self._get_factor(code, 'obv', date)
        if flow_intensity is not None:
            volume_score += min(7, max(0, flow_intensity * 50))

        # 资金流持续性 (5分)
        flow_persist = self._get_factor(code, 'macd_bar', date)
        if flow_persist is not None:
            volume_score += flow_persist * 5

        volume_score = min(volume_score, 20)

        # === 4. 价格形态评分 (0~15) ===
        pattern_score = 0.0

        for pf, pts in [('pattern_strength', 8), ('pattern_reversal', 5),
                        ('pattern_wbottom', 5), ('pattern_pullback', 6)]:
            val = self._get_factor(code, pf, date)
            if val is not None and val > 0:
                pattern_score += pts

        # 价量确认
        price_conf = self._get_factor(code, 'vwap_5', date)
        if price_conf is not None:
            pattern_score += price_conf * 4

        pattern_score = min(pattern_score, 15)

        # === 5. 基本面评分 (0~15) ===
        fundamental_score = 0.0

        # PE合理区间 (5分)
        pe = self._get_factor(code, 'avg_cost', date)
        if pe is not None and 10 < pe < 50:
            fundamental_score += 5

        # PB合理 (5分)
        pb = self._get_factor(code, 'concentration', date)
        if pb is not None and 1 < pb < 10:
            fundamental_score += 5

        # 市值偏好 (5分) — 中小市值加分
        mc = self._get_factor(code, 'profit_ratio', date)
        if mc is not None:
            if 20 < mc < 500:
                fundamental_score += 5
            elif mc <= 20:
                fundamental_score += 3  # 微盘股，风险加分少

        fundamental_score = min(fundamental_score, 15)

        # === 6. 情绪信号评分 (0~10) ===
        sentiment_score = 0.0

        # MXSearch舆情
        mx = self._get_factor(code, 'rsi_14', date)
        if mx is not None:
            sentiment_score += mx  # mx_sentiment范围0~10

        # ML预测
        ml_lgb = self._get_factor(code, 'acceleration', date)
        if ml_lgb is not None and ml_lgb > 0.5:
            sentiment_score += min(5, (ml_lgb - 0.5) * 20)

        sentiment_score = min(sentiment_score, 10)

        # === 7. 安全性评分 (0~10) — 默认10分，扣分制 ===
        safety_score = 10.0

        # 涨幅过高扣分
        pct_chg_5d = self._get_factor(code, 'pct_chg_5d', date)
        if pct_chg_5d is not None and pct_chg_5d > 10:
            safety_score -= 3
        if pct_chg_5d is not None and pct_chg_5d > 20:
            safety_score -= 4

        # RSI超买扣分
        rsi = self._get_factor(code, 'rsi_14', date)
        if rsi is not None and rsi > 80:
            safety_score -= 3

        safety_score = max(0, safety_score)

        # === 综合评分 ===
        w = self.params
        total = (
            momentum_score * w['weight_momentum'] +
            volume_score * w['weight_volume'] +
            pattern_score * w['weight_pattern'] +
            fundamental_score * w['weight_fundamental'] +
            sentiment_score * w['weight_sentiment'] +
            safety_score * w['weight_safety']
        )
        # 归一化到0~100
        max_possible = (
            30 * w['weight_momentum'] +
            20 * w['weight_volume'] +
            15 * w['weight_pattern'] +
            15 * w['weight_fundamental'] +
            10 * w['weight_sentiment'] +
            10 * w['weight_safety']
        )
        if max_possible <= 0:
            return None
        return round(total / max_possible * 100, 1)

    def _make_summary(self, code: str, date: str) -> str:
        """生成评分摘要"""
        parts = []

        sector = self._get_factor(code, 'sector_phase', date)
        if sector is not None:
            if sector >= 5:
                parts.append('板块强势')
            elif sector <= -3:
                parts.append('板块弱势')

        flow = self._get_factor(code, 'obv', date)
        if flow is not None and flow > 0.01:
            parts.append('资金流入')

        pattern = any(
            self._get_factor(code, pf, date) or 0 > 0
            for pf in ['pattern_strength', 'pattern_reversal', 'pattern_pullback']
        )
        if pattern:
            parts.append('形态信号')

        return ' | '.join(parts) if parts else ''

    def _get_market_status(self, date: str) -> str:
        """市场状态判断"""
        benchmark = self.params['benchmark_code']
        pct_chg_5d = self._get_factor(benchmark, 'pct_chg_5d', date)
        if pct_chg_5d is None:
            return 'bull'

        if pct_chg_5d < self.params['stop_threshold']:
            return 'stop'
        if pct_chg_5d < self.params['bear_threshold']:
            return 'bear'
        return 'bull'

    def _get_factor(self, code: str, factor_name: str, date: str):
        if self.feature:
            return self.feature.get_factor(code, factor_name, date)
        return None

    def _is_st(self, code: str) -> bool:
        return code.startswith('st.') or 'st' in code.lower()