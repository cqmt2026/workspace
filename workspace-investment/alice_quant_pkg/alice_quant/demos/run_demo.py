"""AliceQuant 完整演示 - 启动器"""
import sys, os
_pkg = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\alice_quant'
if _pkg not in sys.path:
    sys.path.insert(0, _pkg)
os.chdir(_pkg)

# 先用绝对路径导入所有模块
import importlib
for mod_name in [
    'alice_quant.core.config', 'alice_quant.core.logger',
    'alice_quant.core.signal', 'alice_quant.core.order',
    'alice_quant.core.account', 'alice_quant.core.context',
    'alice_quant.core.result',
    'alice_quant.data.datahub', 'alice_quant.data.version', 'alice_quant.data.snapshot',
    'alice_quant.features.engine', 'alice_quant.features.registry',
    'alice_quant.features.calculators', 'alice_quant.features.store',
    'alice_quant.models.sample_manager', 'alice_quant.models.evaluator',
    'alice_quant.models.registry', 'alice_quant.models.trainers.lightgbm_trainer',
    'alice_quant.strategies.pipeline', 'alice_quant.strategies.trend',
    'alice_quant.strategies.daban', 'alice_quant.strategies.magic_formula',
    'alice_quant.strategies.portfolio',
    'alice_quant.backtest.engine', 'alice_quant.backtest.order_manager',
    'alice_quant.backtest.account_manager', 'alice_quant.backtest.commission',
    'alice_quant.backtest.slippage', 'alice_quant.backtest.performance',
    'alice_quant.backtest.overfitting',
    'alice_quant.execution.signal_handler', 'alice_quant.execution.risk_manager',
    'alice_quant.execution.paper_trading', 'alice_quant.execution.emergency_stop',
    'alice_quant.dashboard.alerts', 'alice_quant.dashboard.monitor',
]:
    importlib.import_module(mod_name)

print(f"Loaded {len([m for m in sys.modules if m.startswith('alice_quant')])} modules")

# 执行演示
demo_path = os.path.join(_pkg, 'demos', 'full_demo.py')
exec(open(demo_path, encoding='utf-8').read())