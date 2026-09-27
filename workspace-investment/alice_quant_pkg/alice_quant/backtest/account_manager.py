"""账户管理器 - 账户状态管理"""
from ..core.account import Account, Position


class AccountManager:
    """账户管理器"""

    def __init__(self, config=None):
        self._config = config

    def initialize(self, initial_capital: float) -> Account:
        """初始化账户"""
        return Account(
            date='',
            total_value=initial_capital,
            cash=initial_capital,
            initial_capital=initial_capital
        )

    def apply_order(self, order, account: Account):
        """应用订单到账户"""
        if order.status != 'filled':
            return

        if order.direction == 'buy':
            self._apply_buy(order, account)
        elif order.direction == 'sell':
            self._apply_sell(order, account)

        # 更新总资产
        account.total_value = account.cash + account.position_value()

    def _apply_buy(self, order, account: Account):
        """应用买入"""
        cost = order.fill_value()
        total_cost = cost + order.commission + order.tax

        if total_cost > account.cash:
            return

        account.cash -= total_cost
        account.commission_paid += order.commission
        account.tax_paid += order.tax

        if order.code in account.positions:
            pos = account.positions[order.code]
            # 加权平均成本
            total_shares = pos.volume + order.filled_volume
            total_cost = pos.volume * pos.avg_cost + order.filled_volume * order.filled_price
            pos.avg_cost = total_cost / total_shares
            pos.volume = total_shares
        else:
            account.positions[order.code] = Position(
                code=order.code,
                volume=order.filled_volume,
                avg_cost=order.filled_price,
                current_price=order.filled_price,
                market_value=order.fill_value()
            )

    def _apply_sell(self, order, account: Account):
        """应用卖出"""
        revenue = order.fill_value()
        total_revenue = revenue - order.commission - order.tax

        account.cash += total_revenue
        account.commission_paid += order.commission
        account.tax_paid += order.tax

        if order.code in account.positions:
            pos = account.positions[order.code]
            pos.volume -= order.filled_volume
            if pos.volume <= 0:
                del account.positions[order.code]
            else:
                pos.update_market_value(order.filled_price)