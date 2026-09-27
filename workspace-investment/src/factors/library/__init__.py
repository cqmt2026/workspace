"""
股票量化因子库 V1.0

因子类别:
- 价值因子 (5 个)
- 成长因子 (5 个)
- 技术因子 (6 个)
- 资金因子 (5 个)
- 情绪因子 (4 个)
- 风险因子 (5 个)

总计：30 个因子
"""

from .factor_base import FactorBase
from .technical_factors import TechnicalFactors
from .moneyflow_factors import MoneyFlowFactors
from .value_factors import ValueFactors
from .growth_factors import GrowthFactors
from .sentiment_factors import SentimentFactors
from .risk_factors import RiskFactors
from .factor_calculator import FactorCalculator

__version__ = "1.0.0"
__all__ = [
    "FactorBase",
    "TechnicalFactors",
    "MoneyFlowFactors",
    "ValueFactors",
    "GrowthFactors",
    "SentimentFactors",
    "RiskFactors",
    "FactorCalculator",
]
