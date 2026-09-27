"""手续费模型 - 佣金+印花税+过户费"""
class CommissionModel:
    """手续费模型"""

    def __init__(self, config=None):
        self._config = config
        self._commission_rate = self._get_rate('backtest.commission_rate', 0.00025)
        self._stamp_tax_rate = self._get_rate('backtest.stamp_tax_rate', 0.001)
        self._transfer_fee_rate = self._get_rate('backtest.transfer_fee_rate', 0.00001)
        self._min_commission = self._get_rate('backtest.min_commission', 5.0)

    def calculate(self, price: float, volume: int, direction: str) -> float:
        """计算手续费

        Args:
            price: 成交价格
            volume: 成交数量
            direction: 方向 (buy/sell)

        Returns:
            手续费金额
        """
        value = price * volume
        commission = value * self._commission_rate
        # 最低佣金
        commission = max(commission, self._min_commission)
        # 过户费（买入和卖出都收）
        transfer_fee = value * self._transfer_fee_rate
        return commission + transfer_fee

    def calculate_tax(self, price: float, volume: int, direction: str) -> float:
        """计算印花税（卖出时收）"""
        if direction == 'sell':
            value = price * volume
            return value * self._stamp_tax_rate
        return 0.0

    def _get_rate(self, key: str, default: float) -> float:
        if self._config:
            return self._config.get(key, default)
        return default