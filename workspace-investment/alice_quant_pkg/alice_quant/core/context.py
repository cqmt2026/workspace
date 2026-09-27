"""回测上下文定义"""

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .account import Account
    from .signal import Signal


@dataclass
class Context:
    """回测上下文

    回测引擎传给策略的运行时信息。
    策略在 on_bar 中通过 context 获取当前回测状态。
    """
    current_date: str = ''                  # 当前回测日期 (YYYY-MM-DD)
    all_dates: List[str] = field(default_factory=list)  # 所有回测日期
    start_date: str = ''                    # 回测开始日期
    end_date: str = ''                      # 回测结束日期
    watch_codes: List[str] = field(default_factory=list)  # 候选股票列表
    account: Optional['Account'] = None     # 当前账户状态 (只读)
    portfolio_signals: List['Signal'] = field(default_factory=list)  # 其他策略本日信号
    data_version: str = ''                  # 当前数据版本
    is_backtesting: bool = True             # 是否在回测中

    def get_dates_before(self, n: int) -> List[str]:
        """获取当前日期前N个交易日

        Args:
            n: 往前推的天数

        Returns:
            日期列表，从早到晚
        """
        if not self.all_dates or self.current_date not in self.all_dates:
            return []
        idx = self.all_dates.index(self.current_date)
        start = max(0, idx - n)
        return self.all_dates[start:idx]

    def get_trading_day_count(self) -> int:
        """回测总交易日数"""
        return len(self.all_dates)

    def get_elapsed_days(self) -> int:
        """当前已运行的天数"""
        if self.current_date in self.all_dates:
            return self.all_dates.index(self.current_date) + 1
        return 0