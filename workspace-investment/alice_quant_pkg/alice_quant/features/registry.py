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