# -*- coding: utf-8 -*-
"""
portfolio - 持仓管理模块
"""

from .positions import PositionManager, add_position, update_position, get_all_positions, get_manager
from .transactions import TransactionManager, add_transaction, get_transactions
from .tracker import NetValueTracker, get_tracker, get_realtime_value
from .daily_report import generate_daily_report, get_latest_report
from .weekly_report import generate_weekly_report
from .price_loader import PriceLoader, get_price_loader, get_realtime_price, get_price_map
from .portfolio_report import generate_portfolio_report

__all__ = [
    # 持仓管理
    'PositionManager',
    'add_position',
    'update_position',
    'get_all_positions',
    'get_manager',
    # 交易记录
    'TransactionManager',
    'add_transaction',
    'get_transactions',
    # 净值追踪
    'NetValueTracker',
    'get_tracker',
    'get_realtime_value',
    # 报告
    'generate_daily_report',
    'generate_weekly_report',
    'get_latest_report',
    # 行情
    'PriceLoader',
    'get_price_loader',
    'get_realtime_price',
    'get_price_map',
    # 一键报告
    'generate_portfolio_report',
]
