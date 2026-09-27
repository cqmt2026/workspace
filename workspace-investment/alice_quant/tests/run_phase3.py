"""Phase 3 验证脚本"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alice_quant.core.config import ConfigManager
from alice_quant.core.logger import Logger
from alice_quant.core.signal import Signal
from alice_quant.core.order import Order
from alice_quant.core.account import Account
from alice_quant.backtest.commission import CommissionModel
from alice_quant.backtest.slippage import SlippageModel
from alice_quant.backtest.order_manager import OrderManager
from alice_quant.backtest.account_manager import AccountManager
from alice_quant.backtest.performance import PerformanceAnalyzer
from alice_quant.backtest.overfitting import OverfitDetector
from alice_quant.backtest.engine import BacktestEngine
from alice_quant.strategies.base import BaseStrategy

config = ConfigManager()
config.load('config/default.yaml')

# Test Commission
cm = CommissionModel(config)
fee = cm.calculate(10.0, 100, 'buy')
tax = cm.calculate_tax(10.0, 100, 'sell')
print(f'Commission: buy_fee={fee:.4f}, sell_tax={tax:.4f}')
assert fee >= 5.0  # 最低佣金
print('  Commission OK')

# Test Slippage
sm = SlippageModel(config)
buy_price = sm.apply(10.0, 'buy')
sell_price = sm.apply(10.0, 'sell')
print(f'Slippage: buy={buy_price:.4f}, sell={sell_price:.4f}')
assert buy_price > 10.0
assert sell_price < 10.0
print('  Slippage OK')

# Test Order Manager
om = OrderManager(config, cm, sm)
order = Order(order_id='O001', date='2026-07-05', code='sz.000001', direction='buy',
              price=10.0, volume=100)
bar_data = {'close': 10.05, 'volume': 10000}
filled = om.execute(order, bar_data, '2026-07-05')
assert filled is not None
assert filled.status == 'filled'
assert filled.filled_price > 10.0
print(f'  OrderManager: filled at {filled.filled_price}')

# Test Account Manager
am = AccountManager(config)
acct = am.initialize(1000000)
assert acct.total_value == 1000000
assert acct.cash == 1000000
am.apply_order(filled, acct)
assert acct.cash < 1000000
assert len(acct.positions) == 1
print(f'  AccountManager: cash={acct.cash:.2f}, pos={acct.position_count()}')

# Test Performance
pa = PerformanceAnalyzer()
result = pa.analyze(
    strategy_name='test', params={},
    start_date='2024-01-01', end_date='2024-12-31',
    account=acct, trades=[{'date':'2024-01-01','code':'sz.000001','direction':'buy','profit':100}],
    all_dates=['2024-01-01','2024-01-02']
)
assert result.strategy_name == 'test'
assert 'sharpe_p_value' in result.significance
print(f'  Performance: sharpe={result.sharpe:.2f}')
print('  Performance OK')

# Test Overfit
od = OverfitDetector()
decay = od.sharpe_decay_test(1.5, 1.0)
assert decay['decay_ratio'] == 1.0/1.5
print(f'  OverfitDetector: decay={decay["decay_ratio"]:.2f}')
print('  OverfitDetector OK')

# Test Strategy Base
class TestStrategy(BaseStrategy):
    def on_bar(self, data, context):
        return [Signal(date='2026-07-05', code='sz.000001', direction='buy',
                       price=10.0, confidence=0.8)]

strategy = TestStrategy('test', {})
signals = strategy.on_bar({}, None)
assert len(signals) == 1
print('  BaseStrategy OK')

# Test Backtest Engine
engine = BacktestEngine(config, logger=Logger(config))
result = engine.run(strategy, '2024-01-01', '2024-01-05', initial_capital=100000)
assert result.strategy_name == 'test'
print(f'  BacktestEngine: trades={result.total_trades}')
print('  BacktestEngine OK')

print('\nPhase 3 all OK')