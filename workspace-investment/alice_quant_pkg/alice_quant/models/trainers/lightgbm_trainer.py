"""LightGBM训练器"""
import numpy as np
from typing import Dict, Optional, Tuple
from .base import BaseTrainer


class LightGBMTrainer(BaseTrainer):
    """LightGBM训练器"""

    def __init__(self, params: Optional[Dict] = None):
        super().__init__(params)
        self._default_params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'max_depth': 6,
            'learning_rate': 0.05,
            'n_estimators': 500,
            'early_stopping_rounds': 50,
            'min_child_samples': 20,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'reg_alpha': 0.1,
            'reg_lambda': 0.1,
            'random_state': 42,
            'verbose': -1,
            'is_unbalance': True,
        }
        self._params = {**self._default_params, **(params or {})}
        self._model = None

    def train(self, X_train, y_train, X_val=None, y_val=None) -> Dict:
        """训练LightGBM模型"""
        try:
            import lightgbm as lgb
        except ImportError:
            raise ImportError("请安装lightgbm: pip install lightgbm")

        train_data = lgb.Dataset(X_train, label=y_train)

        if X_val is not None and y_val is not None:
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            self._model = lgb.train(
                self._params,
                train_data,
                valid_sets=[val_data],
                num_boost_round=self._params['n_estimators'],
                callbacks=[lgb.early_stopping(self._params['early_stopping_rounds']),
                           lgb.log_evaluation(0)]
            )
        else:
            # 无验证集时，不使用早停
            params = {k: v for k, v in self._params.items()
                     if k not in ('early_stopping_rounds',)}
            self._model = lgb.train(
                params,
                train_data,
                num_boost_round=self._params['n_estimators'],
                callbacks=[lgb.log_evaluation(0)]
            )

        self._is_trained = True

        # 特征重要性
        importance = None
        if hasattr(self._model, 'feature_importance'):
            importance = self._model.feature_importance().tolist()

        return {
            'model': self._model,
            'feature_importance': importance,
            'best_iteration': getattr(self._model, 'best_iteration', None),
        }

    def predict(self, X) -> np.ndarray:
        """预测概率"""
        if self._model is None:
            raise ValueError("模型未训练")
        return self._model.predict(X)

    def save(self, path: str):
        """保存模型"""
        if self._model is None:
            raise ValueError("模型未训练")
        import joblib
        joblib.dump(self._model, path)

    def load(self, path: str):
        """加载模型"""
        import joblib
        self._model = joblib.load(path)
        self._is_trained = True