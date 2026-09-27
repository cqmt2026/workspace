"""Phase 4 验证脚本"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from alice_quant.features.registry import FactorRegistry
from alice_quant.features.calculators import TechnicalFactors
from alice_quant.features.store import FactorStore
from alice_quant.features.engine import FeatureEngine
from alice_quant.core.config import ConfigManager

config = ConfigManager()
config.load('config/default.yaml')

# Test FactorRegistry
registry = FactorRegistry()
registry.register('ma_5', 'technical', lambda x: x, description='5日均线')
info = registry.get_info('ma_5')
assert info is not None
assert info.category == 'technical'
assert info.name == 'ma_5'
registry.register('rsi_14', 'technical', lambda x: x)
assert registry.count() == 2
tech_factors = registry.list_factors('technical')
assert len(tech_factors) == 2
print(f'  FactorRegistry: {registry.count()} factors')
print('  FactorRegistry OK')

# Test TechnicalFactors
tf = TechnicalFactors()
close = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
ma5 = tf.ma(close, 5)
assert len(ma5) == 11
assert pd.isna(ma5.iloc[3])  # 前4个为NaN
print(f'  MA5: last={ma5.iloc[-1]:.2f}')

rsi = tf.rsi(close, 5)
assert len(rsi) == 11
print(f'  RSI: last={rsi.iloc[-1]:.2f}')

vol_ratio = tf.volume_ratio(pd.Series([100, 100, 100, 100, 200]), 5)
assert abs(vol_ratio.iloc[-1] - 1.67) < 0.01
print(f'  VolumeRatio: last={vol_ratio.iloc[-1]:.2f}')

pct = tf.pct_change(close)
print(f'  PctChange: last={pct.iloc[-1]:.2f}%')
print('  TechnicalFactors OK')

# Test FactorStore
store = FactorStore(config)
df = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-01', '2024-01-02'],
    'code': ['sz.000001', 'sz.000002', 'sz.000001'],
    'factor_name': ['ma_5', 'ma_5', 'ma_5'],
    'value': [10.5, 11.2, 10.8]
})
store.save_factors_batch(df)

value = store.get_factor('sz.000001', 'ma_5', '2024-01-01')
assert value == 10.5
print(f'  FactorStore: get={value}')

# Test preprocessing
series = pd.Series([1, 2, 3, 100, 4, 5, 6])  # 100是异常值
winsorized = store.preprocess(series, 'winsorize')
assert winsorized.max() < 100
print(f'  Preprocess winsorize: max={winsorized.max():.2f}')

zscored = store.preprocess(series, 'zscore')
assert abs(zscored.mean()) < 0.01
print(f'  Preprocess zscore: mean={zscored.mean():.2f}')

print('  FactorStore OK')

# Test FeatureEngine
engine = FeatureEngine(config)
ok = engine.initialize()
assert ok
assert engine.get_registry().count() > 0
print(f'  FeatureEngine: {engine.get_registry().count()} builtin factors')

# 验证因子分类
for f in engine.list_active_factors():
    print(f'    - [{f.category}] {f.name}: {f.description}')

print('\nPhase 4 all OK')