"""Phase 6+7+8 联合验证脚本"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alice_quant.core.config import ConfigManager
from alice_quant.core.logger import Logger
from alice_quant.core.signal import Signal
from alice_quant.core.account import Account
from alice_quant.core.context import Context
from alice_quant.strategies.pipeline import PipelineStrategy
from alice_quant.strategies.portfolio import PortfolioManager
from alice_quant.execution.signal_handler import SignalHandler
from alice_quant.execution.risk_manager import RiskManager
from alice_quant.execution.paper_trading import PaperTrading
from alice_quant.execution.emergency_stop import EmergencyStop
from alice_quant.dashboard.alerts import AlertSystem, AlertRule
from alice_quant.dashboard.monitor import SystemMonitor

config = ConfigManager()
config.load('config/default.yaml')
logger = Logger(config)

# Test PipelineStrategy
strategy = PipelineStrategy(params={...}, logger=logger)
ctx = Context(
    current_date='2024-01-05',
    all_dates=['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
    watch_codes=['sz.000001', 'sz.000002'],
)
strategy.on_start(ctx)
print('  PipelineStrategy: on_start OK')
print('  PipelineStrategy OK')

# Test PortfolioManager
pm = PortfolioManager(config, logger)
pm.add_strategy(strategy, weight=1.0)
order = pm.resolve_execution_order()
assert len(order) == 1
print(f'  PortfolioManager: order={order}')
acct = Account(date='2024-01-05', total_value=1000000, cash=1000000, initial_capital=1000000)
signals = pm.get_portfolio_signal('2024-01-05', acct, ctx)
print(f'  PortfolioManager: signals={len(signals)}')
print('  PortfolioManager OK')

# Test SignalHandler + RiskManager
handler = SignalHandler(config, logger)
orders = handler.process(signals, acct, '2024-01-05')
print(f'  SignalHandler: orders={len(orders)}')

rm = RiskManager(config, logger)
result = rm.check_before_trade(
    Signal(date='2024-01-05', code='sz.000001', direction='buy', price=10.0, volume=100),
    acct
)
assert result['passed']
print(f'  RiskManager: check={result["passed"]}')
rm.add_to_blacklist('sz.999999')
assert rm._is_blacklisted('sz.999999')
print('  RiskManager OK')
print('  SignalHandler OK')

# Test PaperTrading
pt = PaperTrading(config, logger)
pt.initialize(1000000)
filled = pt.execute(orders, {'close': 10.5, 'volume': 100000}, '2024-01-05')
print(f'  PaperTrading: filled={len(filled)}')
acct2 = pt.get_account()
print(f'  PaperTrading: cash={acct2.cash:.2f}')
pt.save_state()
print('  PaperTrading OK')

# Test EmergencyStop
es = EmergencyStop(logger)
assert not es.is_stopped
es.trigger('测试停止')
assert es.is_stopped
assert es.stop_reason == '测试停止'
es.resume()
assert not es.is_stopped
print('  EmergencyStop OK')

# Test AlertSystem
alerts = AlertSystem(logger)
triggered_count = 0
def test_condition():
    global triggered_count
    triggered_count += 1
    return triggered_count == 1

alerts.add_rule(AlertRule(
    name='test_alert',
    level='WARNING',
    condition=test_condition,
    message='测试告警',
    cooldown_minutes=0
))
events = alerts.check()
assert len(events) == 1
stats = alerts.get_statistics()
assert stats['total'] == 1
print(f'  AlertSystem: events={len(events)}, stats={stats}')
print('  AlertSystem OK')

# Test SystemMonitor
monitor = SystemMonitor(config, logger)
monitor.record_task('test_task', 'success', 1.5)
monitor.record_task('test_task', 'failed', 2.0, 'timeout')
stats = monitor.get_task_stats('test_task')
assert stats['total'] == 2
assert stats['failed'] == 1
print(f'  SystemMonitor: stats={stats}')

health = monitor.health_check()
assert 'status' in health
print(f'  SystemMonitor: health={health["status"]}')
print('  SystemMonitor OK')

print('\nPhase 6+7+8 all OK')