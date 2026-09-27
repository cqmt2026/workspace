"""AliceQuant 自定义异常"""


class AliceQuantError(Exception):
    """框架基础异常"""
    pass


class ConfigError(AliceQuantError):
    """配置相关异常"""
    pass


class DataError(AliceQuantError):
    """数据相关异常"""
    pass


class DataVersionError(DataError):
    """数据版本相关异常"""
    pass


class DataQualityError(DataError):
    """数据质量相关异常"""
    pass


class DataInsufficientError(DataError):
    """数据不足异常"""
    pass


class FactorError(AliceQuantError):
    """因子相关异常"""
    pass


class StrategyError(AliceQuantError):
    """策略相关异常"""
    pass


class CircularDependencyError(StrategyError):
    """策略循环依赖异常"""
    pass


class BacktestError(AliceQuantError):
    """回测相关异常"""
    pass


class RiskError(AliceQuantError):
    """风控相关异常"""
    pass


class ModelError(AliceQuantError):
    """模型相关异常"""
    pass


class EmergencyStopError(AliceQuantError):
    """紧急停止异常"""
    pass