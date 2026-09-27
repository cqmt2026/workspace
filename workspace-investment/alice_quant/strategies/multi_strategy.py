"""
多策略并行引擎 (MultiStrategy Engine)
====================================
火星第一强思路：20套低相关策略并行，各选各的，最终综合投票。

AliceQuant实现：拆Pipeline v2为4个独立子策略 + 1个综合投票层。

子策略（低相关设计）：
  1. 动量策略 — 只看趋势因子（MA排列、RSI、涨幅），不看资金和形态
  2. 资金策略 — 只看量价因子（量比、换手率、资金流），不看趋势和形态
  3. 形态策略 — 只看K线形态因子（突破、反转、W底），不看趋势和资金
  4. 基本面策略 — 只看财务因子（PE/PB/市值），等万得数据就位后启用

综合投票：
  - 各策略独立评分，各选出Top N
  - 综合得分 = 各策略投票加权（命中率高的策略权重高）
  - 最终选股 = 综合得分排序

用法：
    from alice_quant.strategies.multi_strategy import MultiStrategyEngine
    engine = MultiStrategyEngine(feature_engine=feature)
    results = engine.evaluate(candidates, date='2026-07-09')
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import numpy as np


@dataclass
class StrategyVote:
    """单个策略的投票结果"""
    strategy_name: str
    code: str
    score: float        # 0~100
    weight: float       # 当前策略权重（基于近期命中率）
    reason: str = ''


@dataclass
class FinalResult:
    """综合结果"""
    code: str
    final_score: float      # 综合得分 0~100
    votes: List[StrategyVote] = field(default_factory=list)
    consensus: int = 0      # 多少策略投票支持
    avg_score: float = 0.0  # 平均分
    selected: bool = False  # 是否最终入选


class BaseSubStrategy:
    """子策略基类"""

    def __init__(self, name: str, feature_engine=None, params: dict = None):
        self.name = name
        self.feature = feature_engine
        self.params = params or {}
        self.hit_rate = 0.5       # 近期命中率，初始0.5
        self.total_trades = 0
        self.hit_trades = 0

    def score(self, code: str, date: str) -> Optional[float]:
        """评分，返回0~100，None表示排除"""
        raise NotImplementedError

    def get_weight(self) -> float:
        """基于命中率的动态权重"""
        if self.total_trades < 5:
            return 0.5  # 数据不足时给默认权重
        return self.hit_rate

    def update_hit_rate(self, hit: bool):
        """更新命中率"""
        self.total_trades += 1
        if hit:
            self.hit_trades += 1
        self.hit_rate = self.hit_trades / max(self.total_trades, 1)

    def _get_factor(self, code: str, name: str, date: str):
        if self.feature:
            return self.feature.get_factor(code, name, date)
        return None


class MomentumStrategy(BaseSubStrategy):
    """动量策略 — 只看趋势因子

    评分维度：
    - 均线排列 (50分): MA5>MA20>MA60 多头排列
    - 相对强度 (25分): RPS/相对强度
    - 趋势稳定性 (25分): 涨幅均匀，不暴涨暴跌
    """

    def __init__(self, feature_engine=None, params: dict = None):
        super().__init__('动量策略', feature_engine, params)

    def score(self, code: str, date: str) -> Optional[float]:
        score = 0.0

        # 1. 均线排列 (50分)
        ma5 = self._get_factor(code, 'ma_5', date)
        ma20 = self._get_factor(code, 'ma_20', date)
        ma60 = self._get_factor(code, 'ma_60', date)

        if ma5 is None or ma20 is None:
            return None

        if ma5 > ma20:
            score += 20
            if ma60 is not None and ma20 > ma60:
                score += 20  # 完美多头排列
        elif ma5 < ma20:
            return None  # 空头排列直接排除

        # 均线斜率 (10分)
        if ma5 > ma20:
            slope = (ma5 - ma20) / ma20 * 100
            score += min(10, slope * 5)

        # 2. 相对强度 (25分)
        rel_strength = self._get_factor(code, 'relative_strength', date)
        if rel_strength is not None:
            score += min(25, rel_strength * 2.5)

        # 3. 趋势稳定性 (25分)
        pct_chg_5d = self._get_factor(code, 'pct_chg_5d', date)
        pct_chg_10d = self._get_factor(code, 'pct_chg_10d', date)

        if pct_chg_5d is not None and pct_chg_10d is not None:
            # 稳定上涨：5日涨幅不超过10日涨幅的60%
            if pct_chg_10d > 0 and pct_chg_5d / pct_chg_10d < 0.6:
                score += 15  # 加速上涨，趋势强
            elif pct_chg_5d is not None and 0 < pct_chg_5d < 10:
                score += 10  # 温和上涨

        # 涨幅过滤
        pct_chg_1d = self._get_factor(code, 'pct_chg_1d', date)
        if pct_chg_1d is not None and pct_chg_1d > 9.5:
            return None  # 涨停不追

        return min(score, 100)


class VolumeStrategy(BaseSubStrategy):
    """资金策略 — 只看量价因子

    评分维度：
    - 量比 (40分): 放量确认
    - 换手率 (30分): 活跃度适中（3%~15%最佳）
    - 量价协调 (30分): 上涨放量、下跌缩量
    """

    def __init__(self, feature_engine=None, params: dict = None):
        super().__init__('资金策略', feature_engine, params)

    def score(self, code: str, date: str) -> Optional[float]:
        score = 0.0

        # 1. 量比 (40分)
        vol_ratio = self._get_factor(code, 'vol_ratio', date)
        if vol_ratio is None or vol_ratio <= 0.5:
            return None  # 极度缩量直接排除

        if vol_ratio > 3:
            score += 30  # 显著放量
        elif vol_ratio > 1.5:
            score += 35
        elif vol_ratio > 1:
            score += 25
        else:
            score += 15

        # 量比过大扣分（可能是出货）
        if vol_ratio > 8:
            score -= 10

        score = min(score, 40)

        # 2. 换手率 (30分)
        turnover = self._get_factor(code, 'turnover', date)
        if turnover is not None:
            if 3 < turnover < 15:
                score += 30  # 最佳区间
            elif 1 < turnover < 3:
                score += 20
            elif 15 < turnover < 25:
                score += 15
            elif turnover < 1:
                score += 5
            else:
                score += 5  # 换手率过高

        # 3. 量价协调 (30分)
        pct_chg = self._get_factor(code, 'pct_chg_1d', date)
        if pct_chg is not None and vol_ratio is not None:
            if pct_chg > 0 and vol_ratio > 1:
                score += 25  # 上涨放量，健康
            elif pct_chg < 0 and vol_ratio < 1:
                score += 15  # 下跌缩量，惜售
            elif pct_chg > 0 and vol_ratio > 3:
                score += 5   # 放量过大，可能分歧

        return min(score, 100)


class PatternStrategy(BaseSubStrategy):
    """形态策略 — 只看K线形态因子

    评分维度：
    - 突破信号 (40分): 平台突破、趋势突破
    - 反转信号 (30分): W底、V型反转
    - 回踩确认 (30分): 回踩不破支撑
    """

    def __init__(self, feature_engine=None, params: dict = None):
        super().__init__('形态策略', feature_engine, params)

    def score(self, code: str, date: str) -> Optional[float]:
        score = 0.0
        has_signal = False

        # 1. 突破信号 (40分)
        strength = self._get_factor(code, 'pattern_strength', date)
        if strength is not None and strength > 0:
            has_signal = True
            score += min(40, strength * 20)

        # 2. 反转信号 (30分)
        reversal = self._get_factor(code, 'pattern_reversal', date)
        if reversal is not None and reversal > 0:
            has_signal = True
            score += min(30, reversal * 15)

        wbottom = self._get_factor(code, 'pattern_wbottom', date)
        if wbottom is not None and wbottom > 0:
            has_signal = True
            score += 20

        # 3. 回踩确认 (30分)
        pullback = self._get_factor(code, 'pattern_pullback', date)
        if pullback is not None and pullback > 0:
            has_signal = True
            score += min(30, pullback * 15)

        # 4. 价量确认（加分项）
        price_conf = self._get_factor(code, 'price_confirmation', date)
        if price_conf is not None and price_conf > 0:
            score += 10

        # 5. M头预警（扣分项）
        mhead = self._get_factor(code, 'pattern_mhead', date)
        if mhead is not None and mhead > 0:
            score -= 30

        if not has_signal:
            return None  # 无任何形态信号直接排除

        return min(max(score, 0), 100)


class FundamentalStrategy(BaseSubStrategy):
    """基本面策略 — 只看财务因子

    评分维度：
    - PE合理 (30分): 10<PE<50
    - PB合理 (30分): 1<PB<10
    - 市值偏好 (40分): 中小市值（20亿~500亿）
    """

    def __init__(self, feature_engine=None, params: dict = None):
        super().__init__('基本面策略', feature_engine, params)

    def score(self, code: str, date: str) -> Optional[float]:
        score = 0.0
        has_data = False

        # 1. PE (30分)
        pe = self._get_factor(code, 'pe_ttm', date)
        if pe is not None:
            has_data = True
            if 10 < pe < 50:
                score += 30
            elif 5 < pe < 10:
                score += 20
            elif pe < 0:
                return None  # 亏损股直接排除

        # 2. PB (30分)
        pb = self._get_factor(code, 'pb', date)
        if pb is not None:
            has_data = True
            if 1 < pb < 10:
                score += 30
            elif pb < 1:
                score += 10  # 破净
            elif pb > 20:
                score -= 10  # 泡沫

        # 3. 市值 (40分)
        mc = self._get_factor(code, 'market_cap', date)
        if mc is not None:
            has_data = True
            if 20 < mc < 500:
                score += 40  # 中小市值
            elif 500 < mc < 1000:
                score += 25
            elif mc < 20:
                score += 15  # 微盘股
            elif mc > 1000:
                score += 10  # 大盘股

        if not has_data:
            return None  # 无任何财务数据，暂时不参与

        return min(score, 100)


class MultiStrategyEngine:
    """多策略并行引擎"""

    def __init__(self, feature_engine=None, strategies: List[str] = None):
        self.feature = feature_engine

        # 初始化子策略
        strategy_map = {
            'momentum': MomentumStrategy,
            'volume': VolumeStrategy,
            'pattern': PatternStrategy,
            'fundamental': FundamentalStrategy,
        }

        if strategies is None:
            strategies = ['momentum', 'volume', 'pattern']

        self.strategies = {}
        for name in strategies:
            cls = strategy_map.get(name)
            if cls:
                self.strategies[name] = cls(feature_engine)

        # 投票权重（基于历史命中率动态调整）
        self.vote_weights = {name: 0.5 for name in self.strategies}

        # 历史记录
        self.history = []

    def evaluate(self, candidates: List[dict], date: str,
                 top_n: int = 5, min_consensus: int = 2) -> List[FinalResult]:
        """
        多策略并行评估

        Args:
            candidates: [{'code': str, 'price': float, ...}, ...]
            date: 日期
            top_n: 每个策略选Top N
            min_consensus: 最少需要多少策略投票

        Returns:
            List[FinalResult]: 综合结果
        """
        if not candidates or not self.strategies:
            return []

        # 各策略独立评分
        all_votes = {}  # code -> [StrategyVote, ...]
        for s_name, strategy in self.strategies.items():
            weight = strategy.get_weight()
            scored = []
            for c in candidates:
                code = c.get('code', '')
                s = strategy.score(code, date)
                if s is not None:
                    scored.append((code, s))

            scored.sort(key=lambda x: x[1], reverse=True)
            for code, s in scored[:top_n]:
                if code not in all_votes:
                    all_votes[code] = []
                all_votes[code].append(StrategyVote(
                    strategy_name=s_name,
                    code=code,
                    score=s,
                    weight=weight,
                    reason=f'{s_name}: {s:.0f}分'
                ))

        # 综合计算
        results = []
        for code, votes in all_votes.items():
            consensus = len(votes)
            if consensus < min_consensus:
                continue

            # 加权综合得分
            weighted_sum = sum(v.score * v.weight for v in votes)
            weight_sum = sum(v.weight for v in votes)
            final_score = weighted_sum / weight_sum if weight_sum > 0 else 0

            # 平均分
            avg_score = np.mean([v.score for v in votes])

            results.append(FinalResult(
                code=code,
                final_score=round(final_score, 1),
                votes=votes,
                consensus=consensus,
                avg_score=round(avg_score, 1),
            ))

        # 按综合得分排序
        results.sort(key=lambda x: x.final_score, reverse=True)

        # 标记最终入选
        for r in results[:top_n]:
            r.selected = True

        return results

    def record_result(self, results: List[FinalResult], date: str):
        """记录评估结果供复盘使用"""
        self.history.append({
            'date': date,
            'results': results,
            'timestamp': __import__('datetime').datetime.now().isoformat(),
        })

    def update_weights(self, date: str, hit_codes: set):
        """根据命中结果更新各策略权重

        Args:
            date: 日期
            hit_codes: 当日命中（次日上涨）的股票代码集合
        """
        for s_name, strategy in self.strategies.items():
            hit = 0
            total = 0
            for record in self.history:
                if record['date'] == date:
                    for r in record['results']:
                        for v in r.votes:
                            if v.strategy_name == s_name:
                                total += 1
                                if r.code in hit_codes:
                                    hit += 1
            if total > 0:
                strategy.update_hit_rate(hit / total >= 0.5)

    def get_strategy_summary(self) -> List[dict]:
        """获取各策略状态"""
        return [{
            'name': name,
            'hit_rate': s.hit_rate,
            'total_trades': s.total_trades,
            'hit_trades': s.hit_trades,
            'weight': s.get_weight(),
        } for name, s in self.strategies.items()]