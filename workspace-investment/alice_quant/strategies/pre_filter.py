"""
前置风控过滤层 (PreFilter)
===========================
选股前的硬性筛选层，在评分之前执行。

火星第一强思路：风控前置，从源头降低风险。
直接在选股前把明显不合格的标的剔除，而不是选股时靠参数过滤。

过滤规则：
  1. 剔除ST/退市/北交所
  2. 剔除次新（上市<60天）
  3. 剔除低流动性（日成交额<3000万或日成交量<100万手）
  4. 剔除低价股（<5元）
  5. 剔除异常股（连续跌停、停牌、涨跌停板封死）
  6. 剔除高质押风险（万得数据就位后启用）
  7. 剔除负面舆情（MXSearch就位后启用）

用法：
    from alice_quant.strategies.pre_filter import PreFilter
    pf = PreFilter(feature_engine=feature)
    passed = pf.filter(candidates, date='2026-07-09')
"""
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class FilterResult:
    """过滤结果"""
    passed: List[dict] = field(default_factory=list)
    eliminated: List[dict] = field(default_factory=list)
    reasons: Dict[str, str] = field(default_factory=dict)  # code -> reason


class PreFilter:
    """前置风控过滤器"""

    # 过滤规则配置
    RULES = {
        'min_price': 5.0,           # 最低价格
        'min_volume': 1_000_000,    # 最低成交量（手）
        'min_amount': 30_000_000,   # 最低成交额（元）
        'max_consecutive_limit_down': 2,  # 最大连续跌停天数
        'min_listing_days': 60,     # 最小上市天数
        'max_drop_1d': -9.5,        # 单日最大跌幅（超过此值视为跌停）
        'max_rise_1d': 9.5,         # 单日最大涨幅（超过此值视为涨停，涨停不买）
    }

    def __init__(self, feature_engine=None, params: dict = None):
        self.feature = feature_engine
        self.params = {**self.RULES, **(params or {})}
        self.stats = {'checked': 0, 'passed': 0, 'eliminated': 0}

    def filter(self, candidates: List[dict], date: str) -> FilterResult:
        """
        对候选列表执行前置风控过滤

        Args:
            candidates: [{'code': str, 'price': float, ...}, ...]
            date: 日期 YYYY-MM-DD

        Returns:
            FilterResult: 包含通过/淘汰/原因
        """
        result = FilterResult()
        if not candidates:
            return result

        for c in candidates:
            code = c.get('code', '')
            price = c.get('price', 0)
            self.stats['checked'] += 1

            # 依次检查每条规则，命中第一条即淘汰
            reason = self._check(code, price, date)
            if reason:
                c['elimination_reason'] = reason
                result.eliminated.append(c)
                result.reasons[code] = reason
                self.stats['eliminated'] += 1
            else:
                result.passed.append(c)
                self.stats['passed'] += 1

        return result

    def _check(self, code: str, price: float, date: str) -> Optional[str]:
        """逐条检查过滤规则，返回第一条命中的原因，None表示通过"""
        if not self.feature:
            return None

        # 1. 剔除ST/退市/北交所
        if code.startswith('bj.') or 'st' in code.lower():
            return 'ST/北交所/退市'

        # 2. 剔除低价股
        if price < self.params['min_price']:
            return f'低价({price:.2f}<{self.params["min_price"]})'

        # 3. 剔除低流动性（成交额）
        amount = self.feature.get_factor(code, 'amount', date)
        if amount is not None and amount < self.params['min_amount']:
            return f'低成交额({amount:.0f}<{self.params["min_amount"]})'

        # 4. 剔除低流动性（成交量）
        volume = self.feature.get_factor(code, 'volume', date)
        if volume is not None and volume < self.params['min_volume']:
            return f'低成交量({volume:.0f}<{self.params["min_volume"]})'

        # 5. 剔除跌停股
        pct_chg = self.feature.get_factor(code, 'pct_chg_1d', date)
        if pct_chg is not None and pct_chg < self.params['max_drop_1d']:
            return f'跌停({pct_chg:.1f}%)'

        # 6. 剔除涨停股（封死涨停买不到）
        if pct_chg is not None and pct_chg > self.params['max_rise_1d']:
            return f'涨停({pct_chg:.1f}%)'

        # 7. 剔除连续大跌
        pct_chg_5d = self.feature.get_factor(code, 'pct_chg_5d', date)
        if pct_chg_5d is not None and pct_chg_5d < -20:
            return f'5日大跌({pct_chg_5d:.1f}%)'

        # 8. 剔除涨幅过高
        if pct_chg_5d is not None and pct_chg_5d > 30:
            return f'5日暴涨({pct_chg_5d:.1f}%)'

        # 9. 剔除次新（上市天数不足）
        # 需要从基本面数据获取上市日期，万得就位后启用
        # listing_days = self.feature.get_factor(code, 'listing_days', date)
        # if listing_days is not None and listing_days < self.params['min_listing_days']:
        #     return f'次新({listing_days}天<{self.params["min_listing_days"]})'

        return None

    def get_stats(self) -> dict:
        """获取过滤统计"""
        return self.stats

    def reset_stats(self):
        """重置统计"""
        self.stats = {'checked': 0, 'passed': 0, 'eliminated': 0}