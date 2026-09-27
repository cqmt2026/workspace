"""订单管理器 - 订单生命周期管理"""
from typing import Optional, List
from ..core.order import Order
from ..core.account import Account
from .commission import CommissionModel
from .slippage import SlippageModel


class OrderManager:
    """订单管理器"""

    def __init__(self, config=None, commission=None, slippage=None):
        self._config = config
        self._commission = commission or CommissionModel(config)
        self._slippage = slippage or SlippageModel(config)
        self._orders: List[Order] = []
        self._volume_limit_ratio = self._get_volume_limit()

    def execute(self, order: Order, bar_data: dict, date: str) -> Optional[Order]:
        """执行订单

        Args:
            order: 待执行订单
            bar_data: 当日行情数据
            date: 日期

        Returns:
            成交后的订单，未成交返回None
        """
        # 成交量限制检查
        if not self._check_volume_limit(order, bar_data):
            return None

        # 计算成交价格（含滑点）
        if order.direction == 'buy':
            filled_price = bar_data.get('close', order.price)
        else:
            filled_price = bar_data.get('close', order.price)

        filled_price = self._slippage.apply(filled_price, order.direction)

        # 计算手续费
        commission = self._commission.calculate(filled_price, order.volume, order.direction)
        tax = self._commission.calculate_tax(filled_price, order.volume, order.direction)
        slippage_cost = abs(filled_price - order.price) * order.volume

        # 更新订单
        order.status = 'filled'
        order.filled_price = filled_price
        order.filled_volume = order.volume
        order.commission = commission
        order.tax = tax
        order.slippage = slippage_cost

        self._orders.append(order)
        return order

    def cancel(self, order_id: str) -> bool:
        """取消订单"""
        for order in self._orders:
            if order.order_id == order_id and order.is_pending():
                order.status = 'cancelled'
                return True
        return False

    def get_pending_orders(self) -> List[Order]:
        """获取待成交订单"""
        return [o for o in self._orders if o.is_pending()]

    def _check_volume_limit(self, order: Order, bar_data: dict) -> bool:
        """成交量限制检查"""
        daily_volume = bar_data.get('volume', 0)
        if daily_volume <= 0:
            return True
        if order.volume > daily_volume * self._volume_limit_ratio:
            return False
        return True

    def _get_volume_limit(self) -> float:
        if self._config:
            return self._config.get('backtest.volume_limit.single', 0.1)
        return 0.1