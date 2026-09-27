"""Phase 5 验证脚本"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from alice_quant.models.sample_manager import SampleManager, SampleConfig
from alice_quant.models.trainers.base import BaseTrainer
from alice_quant.models.trainers.lightgbm_trainer import LightGBMTrainer
from alice_quant.models.evaluator import ModelEvaluator
from alice_quant.models.registry import ModelRegistry
from alice_quant.core.config import ConfigManager

config = ConfigManager()
config.load('config/default.yaml')

# Test SampleManager
sm = SampleManager(SampleConfig(positive_threshold=0.03, negative_threshold=-0.03))
import pandas as pd
data = pd.DataFrame({
    'date': ['2024-01-01'] * 100,
    'code': [f'sz.{i:06d}' for i in range(100)],
    'return_N': np.random.randn(100) * 0.05,
    'feature_1': np.random.randn(100),
    'feature_2': np.random.randn(100),
})
X, y = sm.build_samples(data, ['feature_1', 'feature_2'])
assert len(X) == 100
print(f'  SampleManager: X={X.shape}, y={y.shape}')
print(f'    positive={sum(y==1)}, negative={sum(y==0)}')
print('  SampleManager OK')

# Test Train/Val/Test split
dates = data['date'].tolist()
result = sm.train_val_test_split(X, y, dates)
assert len(result) == 6
print(f'  Split: train={len(result[0])}, val={len(result[2])}, test={len(result[4])}')
print('  TrainValTestSplit OK')

# Test LightGBMTrainer
trainer = LightGBMTrainer({'n_estimators': 50, 'verbose': -1})
record = trainer.train(X, y)
assert trainer.is_trained()
preds = trainer.predict(X)
assert len(preds) == len(y)
assert all(0 <= p <= 1 for p in preds)
print(f'  LightGBMTrainer: preds mean={preds.mean():.3f}')
print('  LightGBMTrainer OK')

# Test save/load
import os
os.makedirs('data/models/', exist_ok=True)
trainer.save('data/models/test_model.pkl')
trainer2 = LightGBMTrainer()
trainer2.load('data/models/test_model.pkl')
assert trainer2.is_trained()
preds2 = trainer2.predict(X)
assert np.allclose(preds, preds2)
print('  Save/Load OK')

# Test ModelEvaluator
evaluator = ModelEvaluator()
y_true = (np.random.rand(100) > 0.5).astype(int)
y_pred = np.random.rand(100)
cls_result = evaluator.evaluate_classification(y_true, y_pred)
assert 'auc' in cls_result
assert 'accuracy' in cls_result
print(f'  Evaluator: auc={cls_result["auc"]:.3f}')

ranking_result = evaluator.evaluate_ranking(y_true, y_pred)
assert 'rank_ic' in ranking_result
print(f'  Evaluator: rank_ic={ranking_result["rank_ic"]:.3f}')

gen_result = evaluator.evaluate_generalization(
    {'auc': 0.85}, {'auc': 0.72}
)
assert 'overfit_risk' in gen_result
print(f'  Evaluator: overfit={gen_result["overfit_risk"]}')
print('  ModelEvaluator OK')

# Test ModelRegistry
reg = ModelRegistry(config)
v1 = reg.register('test_model', 'lightgbm', {'lr': 0.05})
assert v1 == 'v1.0.0'
v2 = reg.register('test_model', 'lightgbm', {'lr': 0.1})
assert v2 == 'v1.0.1'
print(f'  Registry: {v1}, {v2}')

reg.update_status('test_model', v1, 'online')
online = reg.get_online_model('test_model')
assert online is not None
assert online['version'] == v1

reg.update_metrics('test_model', v1, {'auc': 0.85, 'rank_ic': 0.03})
info = reg.get_model_info('test_model', v1)
assert info['metrics']['auc'] == 0.85

models = reg.list_models('test_model')
assert len(models) >= 2
print(f'  Registry: {len(models)} versions')
print('  ModelRegistry OK')

# Cleanup
import os
if os.path.exists('data/models/test_model.pkl'):
    os.remove('data/models/test_model.pkl')

print('\nPhase 5 all OK')