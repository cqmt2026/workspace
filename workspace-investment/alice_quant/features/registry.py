"""因子注册中心 - 因子定义/注册/查询"""
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FactorInfo:
    """因子元信息"""
    name: str                       # 因子名称
    category: str                   # 类别: technical/fundamental/money_flow/sentiment/macro/ml
    description: str = ''           # 描述
    params: dict = field(default_factory=dict)  # 计算参数
    dependencies: List[str] = field(default_factory=list)  # 依赖的因子
    update_frequency: str = 'daily'  # 更新频率
    version: int = 1                # 版本号
    created_at: str = ''            # 创建时间


class FactorRegistry:
    """因子注册中心"""

    def __init__(self):
        self._factors: Dict[str, FactorInfo] = {}
        self._calculators: Dict[str, Callable] = {}
        self._register_defaults()

    def _register_defaults(self):
        """注册默认因子"""
        from .calculators.technical import TechnicalFactors
        from .calculators.advanced import MomentumFactors, ChipFactors

        tf = TechnicalFactors()
        mf = MomentumFactors()
        cf = ChipFactors()

        self.register('ma_5', 'technical', tf.ma, '5日均线', {'window': 5})
        self.register('ma_20', 'technical', tf.ma, '20日均线', {'window': 20})
        self.register('ma_60', 'technical', tf.ma, '60日均线', {'window': 60})
        self.register('rsi_14', 'technical', tf.rsi, '14日RSI', {'window': 14})
        self.register('vol_ratio', 'technical', tf.volume_ratio, '量比', {'window': 5})
        self.register('pct_chg_1d', 'technical', tf.pct_change, '1日涨幅', {'periods': 1})
        self.register('pct_chg_5d', 'technical', tf.pct_change, '5日涨幅', {'periods': 5})
        self.register('atr_14', 'technical', tf.atr, '14日ATR', {'window': 14})
        self.register('obv', 'technical', tf.obv, 'OBV能量潮')
        self.register('wr_14', 'technical', tf.wr, '14日威廉指标', {'window': 14})
        self.register('cci_20', 'technical', tf.cci, '20日CCI', {'window': 20})
        self.register('vwap_5', 'technical', tf.vwap, '5日VWAP', {'window': 5})
        self.register('volatility_20', 'technical', tf.volatility, '20日波动率', {'window': 20})
        self.register('macd_bar', 'technical', mf.macd_bar, 'MACD柱状图')
        self.register('macd_cross', 'technical', mf.macd_cross, 'MACD金叉/死叉')
        self.register('macd_second_peak', 'technical', mf.macd_second_peak, 'MACD二次信号')
        self.register('acceleration', 'technical', mf.acceleration, '涨速比')
        self.register('breakout_strength', 'technical', mf.breakout_strength, '突破强度')
        self.register('avg_cost', 'technical', cf.avg_cost, '平均持仓成本', {'window': 60})
        self.register('profit_ratio', 'technical', cf.profit_ratio, '获利盘比例')
        self.register('concentration', 'technical', cf.concentration, '筹码集中度', {'window': 20})

        # 板块因子（无统一计算器，由daily_factor_compute单独计算）
        self.register('relative_strength', 'sector', None, '相对强度')
        self.register('sector_phase', 'sector', None, '板块阶段')
        self.register('sector_rps_5d', 'sector', None, '板块RPS')

    def register(self, name: str, category: str, calculator: Callable,
                 description: str = '', params: dict = None,
                 dependencies: list = None,
                 update_frequency: str = 'daily') -> 'FactorRegistry':
        """注册因子

        Args:
            name: 因子名称
            category: 类别
            calculator: 计算函数
            description: 描述
            params: 计算参数
            dependencies: 依赖的因子列表
            update_frequency: 更新频率

        Returns:
            self
        """
        info = FactorInfo(
            name=name,
            category=category,
            description=description,
            params=params or {},
            dependencies=dependencies or [],
            update_frequency=update_frequency,
            version=1,
            created_at=datetime.now().isoformat()
        )
        self._factors[name] = info
        self._calculators[name] = calculator
        return self

    def unregister(self, name: str) -> bool:
        """注销因子"""
        if name in self._factors:
            del self._factors[name]
            del self._calculators[name]
            return True
        return False

    def get_info(self, name: str) -> Optional[FactorInfo]:
        """获取因子信息"""
        return self._factors.get(name)

    def get_calculator(self, name: str) -> Optional[Callable]:
        """获取因子计算函数"""
        return self._calculators.get(name)

    def list_factors(self, category: Optional[str] = None) -> List[FactorInfo]:
        """列出因子

        Args:
            category: 类别过滤

        Returns:
            因子信息列表
        """
        if category:
            return [f for f in self._factors.values() if f.category == category]
        return list(self._factors.values())

    def list_categories(self) -> List[str]:
        """列出所有类别"""
        return list(set(f.category for f in self._factors.values()))

    def count(self) -> int:
        """因子数量"""
        return len(self._factors)

    def has_factor(self, name: str) -> bool:
        """检查因子是否存在"""
        return name in self._factors