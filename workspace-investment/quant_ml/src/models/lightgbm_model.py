# -*- coding: utf-8 -*-
"""
LightGBM模型封装
"""
import numpy as np
import lightgbm as lgb
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, precision_score, recall_score


class LightGBMModel:
    """LightGBM分类器封装"""

    def __init__(self, config: dict):
        self.cfg = config['model']['lightgbm']
        self.feature_names = []
        self._model = None

    def build_params(self) -> dict:
        """构建LightGBM参数字典"""
        return dict(self.cfg)

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_early_stop: np.ndarray,
        y_early_stop: np.ndarray,
        feature_names: list,
        callbacks: list = None,
    ):
        """训练模型"""
        self.feature_names = feature_names

        params = self.build_params()
        # 移除early stopping不需要的参数
        params.pop('n_estimators', None)

        train_data = lgb.Dataset(X_train, label=y_train, feature_name=feature_names)
        es_data = lgb.Dataset(X_early_stop, label=y_early_stop, reference=train_data)

        self._model = lgb.train(
            params,
            train_data,
            num_boost_round=self.cfg.get('n_estimators', 500),
            valid_sets=[train_data, es_data],
            valid_names=['train', 'early_stop'],
            callbacks=callbacks or [],
        )
        return self._model

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Model not trained yet")
        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """返回概率（与predict相同，LightGBM二分类输出即概率）"""
        return self.predict(X)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> dict:
        """评估模型"""
        pred_prob = self.predict(X)
        pred = (pred_prob > 0.5).astype(int)
        acc = accuracy_score(y, pred)
        auc = roc_auc_score(y, pred_prob)
        f1 = f1_score(y, pred)
        prec = precision_score(y, pred)
        rec = recall_score(y, pred)
        return {
            'accuracy': float(acc),
            'auc': float(auc),
            'f1': float(f1),
            'precision': float(prec),
            'recall': float(rec),
        }

    def feature_importance(self) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Model not trained yet")
        return self._model.feature_importance()

    def best_iteration(self) -> int:
        if self._model is None:
            return 0
        return self._model.best_iteration

    def save(self, path: str):
        if self._model is None:
            raise RuntimeError("Model not trained yet")
        self._model.save_model(path)

    def load(self, path: str):
        self._model = lgb.Booster(model_file=path)
