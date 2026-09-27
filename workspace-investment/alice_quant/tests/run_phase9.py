"""Phase 9 集成测试 - 端到端回测"""
import sys, os, importlib.util

# 直接加载alice_quant包（绕过sys.path问题）
_pkg_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\alice_quant'
if _pkg_path not in sys.path:
    sys.path.insert(0, _pkg_path)
os.chdir(_pkg_path)

# 强制导入alice_quant包
import alice_quant
import alice_quant.core
import alice_quant.core.config
import alice_quant.core.logger
import alice_quant.core.signal
import alice_quant.core.order
import alice_quant.core.account
import alice_quant.core.context
import alice_quant.core.result
import alice_quant.strategies
import alice_quant.strategies.pipeline
import alice_quant.strategies.portfolio
import alice_quant.backtest
import alice_quant.backtest.engine
import alice_quant.backtest.performance
import alice_quant.backtest.overfitting
import alice_quant.execution
import alice_quant.execution.signal_handler
import alice_quant.execution.risk_manager
import alice_quant.execution.emergency_stop
import alice_quant.dashboard
import alice_quant.dashboard.alerts
import alice_quant.dashboard.monitor

import numpy as np
from alice_quant.core.config import ConfigManager
from alice_quant.core.logger import Logger
from alice_quant.core.signal import Signal
from alice_quant.core.result import BacktestResult
from alice_quant.strategies.pipeline import PipelineStrategy
from alice_quant.strategies.portfolio import PortfolioManager
from alice_quant.backtest.engine import BacktestEngine
from alice_quant.backtest.performance import PerformanceAnalyzer
from alice_quant.backtest.overfitting import OverfitDetector
from alice_quant.execution.signal_handler import SignalHandler
from alice_quant.execution.risk_manager import RiskManager
from alice_quant.execution.emergency_stop import EmergencyStop
from alice_quant.dashboard.alerts import AlertSystem, AlertRule
from alice_quant.dashboard.monitor import SystemMonitor


def test_quick_summary():
    print("[1] 模块导入验证...", end=' ')
    from alice_quant.core.config import ConfigManager
    from alice_quant.core.logger import Logger
    from alice_quant.core.signal import Signal
    from alice_quant.core.order import Order
    from alice_quant.core.account import Account
    from alice_quant.core.context import Context
    from alice_quant.core.result import BacktestResult
    from alice_quant.data.datahub import DataHub
    from alice_quant.data.version import DataVersionManager
    from alice_quant.data.snapshot import SnapshotManager
    from alice_quant.features.engine import FeatureEngine
    from alice_quant.features.registry import FactorRegistry
    from alice_quant.features.calculators import TechnicalFactors
    from alice_quant.models.sample_manager import SampleManager
    from alice_quant.models.evaluator import ModelEvaluator
    from alice_quant.models.registry import ModelRegistry
    from alice_quant.strategies.base import BaseStrategy
    from alice_quant.strategies.pipeline import PipelineStrategy
    from alice_quant.strategies.portfolio import PortfolioManager
    from alice_quant.backtest.engine import BacktestEngine
    from alice_quant.backtest.performance import PerformanceAnalyzer
    from alice_quant.backtest.overfitting import OverfitDetector
    from alice_quant.execution.signal_handler import SignalHandler
    from alice_quant.execution.risk_manager import RiskManager
    from alice_quant.execution.paper_trading import PaperTrading
    from alice_quant.execution.emergency_stop import EmergencyStop
    from alice_quant.dashboard.alerts import AlertSystem
    from alice_quant.dashboard.monitor import SystemMonitor
    print("OK (25 modules)")


def test_data_quality():
    print("[2] 数据质量测试...", end=' ')
    config = ConfigManager()
    config.load('config/default.yaml')
    from alice_quant.data.version import DataVersionManager
    vm = DataVersionManager(config)
    v1 = vm.create_version({'stock_count': 5000, 'quality_score': 95})
    v2 = vm.create_version({'stock_count': 5100, 'quality_score': 90})
    info = vm.get_version_info(v1)
    assert info['data']['quality_score'] == 95
    diff = vm.compare_versions(v1, v2)
    assert 'stock_count' in diff.get('data_diff', {})
    from alice_quant.data.snapshot import SnapshotManager
    import pandas as pd
    sm = SnapshotManager()
    df = pd.DataFrame({'date': ['2024-01-01','2024-01-02','2024-01-03'], 'v': [1,2,3]})
    f = sm.filter_by_date(df, '2024-01-02')
    assert len(f) == 2
    assert not sm.validate_no_future_data(df, '2024-01-02')
    print("OK")


def test_component_integration():
    print("[3] 组件协作测试...", end=' ')
    config = ConfigManager()
    config.load('config/default.yaml')
    logger = Logger(config)
    strategy = PipelineStrategy(logger=logger)
    pm = PortfolioManager(config, logger)
    pm.add_strategy(strategy)
    order = pm.resolve_execution_order()
    assert len(order) == 1
    handler = SignalHandler(config, logger)
    rm = RiskManager(config, logger)
    acct = type('obj', (object,), {'total_value': 1000000, 'cash': 1000000})()
    assert rm.check_before_trade(
        Signal(date='2024-01-05', code='sz.000001', direction='buy', price=10.0, volume=100), acct
    )['passed']
    es = EmergencyStop(logger)
    es.trigger('test')
    assert es.is_stopped
    es.resume()
    assert not es.is_stopped
    alerts = AlertSystem(logger)
    count = [0]
    alerts.add_rule(AlertRule('test', 'INFO', lambda: count[0]==0, 'test'))
    events = alerts.check()
    count[0] += 1
    assert len(events) == 1
    monitor = SystemMonitor(config, logger)
    monitor.record_task('test', 'success', 0.5)
    health = monitor.health_check()
    assert 'status' in health
    print("OK")


def test_model_pipeline():
    print("[4] 模型训练测试...", end=' ')
    config = ConfigManager()
    config.load('config/default.yaml')
    from alice_quant.models.sample_manager import SampleManager, SampleConfig
    from alice_quant.models.trainers.lightgbm_trainer import LightGBMTrainer
    from alice_quant.models.evaluator import ModelEvaluator
    from alice_quant.models.registry import ModelRegistry
    import pandas as pd
    sm = SampleManager(SampleConfig(positive_threshold=0.02, negative_threshold=-0.02))
    np.random.seed(42)
    data = pd.DataFrame({
        'date': ['2024-01-01']*200,
        'code': [f'sz.{i:06d}' for i in range(200)],
        'return_N': np.random.randn(200)*0.04,
        'ma_5': np.random.randn(200),
        'vol_ratio': np.random.rand(200)*3,
    })
    X, y = sm.build_samples(data, ['ma_5', 'vol_ratio'])
    assert len(X) == 200
    # Convert y to binary classification labels
    y_binary = (y > 0).astype(int)
    trainer = LightGBMTrainer({'n_estimators': 30, 'verbose': -1})
    trainer.train(X, y_binary)
    preds = trainer.predict(X)
    assert len(preds) == 200
    evaluator = ModelEvaluator()
    cls_result = evaluator.evaluate_classification(y_binary, preds)
    assert 'auc' in cls_result
    ranking = evaluator.evaluate_ranking(y, preds)
    assert 'rank_ic' in ranking
    reg = ModelRegistry(config)
    v = reg.register('test_m', 'lightgbm', {'lr': 0.05})
    reg.update_metrics('test_m', v, {'auc': cls_result['auc']})
    reg.update_status('test_m', v, 'online')
    online = reg.get_online_model('test_m')
    assert online is not None
    print("OK")


def test_backtest():
    print("[5] 回测引擎测试...", end=' ')
    config = ConfigManager()
    config.load('config/default.yaml')
    logger = Logger(config)
    strategy = PipelineStrategy(logger=logger)
    engine = BacktestEngine(config, logger=logger)
    result = engine.run(strategy, '2024-01-01', '2024-12-31', initial_capital=1000000)
    assert result.strategy_name == 'pipeline'
    assert 'sharpe_p_value' in result.significance
    summary = result.summary()
    assert 'pipeline' in summary
    os.makedirs('reports', exist_ok=True)
    result.save_report('reports/test_report.html')
    result.export_trades('reports/test_trades.csv')
    assert os.path.exists('reports/test_report.html')
    print(f"OK (trades={result.total_trades}, sharpe={result.sharpe:.2f})")


def test_execution_layer():
    print("[6] 执行层测试...", end=' ')
    config = ConfigManager()
    config.load('config/default.yaml')
    logger = Logger(config)
    from alice_quant.execution.paper_trading import PaperTrading
    pt = PaperTrading(config, logger)
    pt.initialize(1000000)
    acct = pt.get_account()
    assert acct.total_value == 1000000
    pt.save_state()
    print("OK")


if __name__ == '__main__':
    print("=" * 50)
    print("Phase 9 集成测试")
    print("=" * 50)
    test_quick_summary()
    test_data_quality()
    test_component_integration()
    test_model_pipeline()
    test_backtest()
    test_execution_layer()
    print("=" * 50)
    print("Phase 9 全部通过!")
    print("=" * 50)