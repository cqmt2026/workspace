"""模型评估器"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.metrics import (roc_auc_score, accuracy_score, precision_score,
                             recall_score, f1_score, confusion_matrix)
from scipy import stats


class ModelEvaluator:
    """模型评估器"""

    @staticmethod
    def evaluate_classification(y_true, y_pred_prob: np.ndarray,
                                threshold: float = 0.5) -> Dict:
        """分类模型评估

        Args:
            y_true: 真实标签
            y_pred_prob: 预测概率
            threshold: 分类阈值

        Returns:
            评估指标 dict
        """
        y_pred = (y_pred_prob >= threshold).astype(int)

        result = {
            'auc': roc_auc_score(y_true, y_pred_prob),
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0),
        }

        # 混淆矩阵
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        result['tn'] = int(tn)
        result['fp'] = int(fp)
        result['fn'] = int(fn)
        result['tp'] = int(tp)

        return result

    @staticmethod
    def evaluate_ranking(y_true, y_pred_prob: np.ndarray) -> Dict:
        """排序模型评估

        Args:
            y_true: 真实标签/收益
            y_pred_prob: 预测概率

        Returns:
            评估指标 dict
        """
        from scipy.stats import spearmanr

        rank_ic, p_value = spearmanr(y_pred_prob, y_true)

        # 分组收益
        n = len(y_pred_prob)
        if n >= 10:
            groups = 10
            group_size = n // groups
            group_returns = []
            for i in range(groups):
                start = i * group_size
                end = start + group_size if i < groups - 1 else n
                group_returns.append(np.mean(y_true[start:end]))
            top_minus_bottom = group_returns[0] - group_returns[-1]
        else:
            group_returns = [np.mean(y_true)]
            top_minus_bottom = 0

        return {
            'rank_ic': rank_ic,
            'rank_ic_p_value': p_value,
            'group_returns': group_returns,
            'top_minus_bottom': top_minus_bottom,
        }

    @staticmethod
    def evaluate_generalization(train_metrics: Dict, test_metrics: Dict) -> Dict:
        """泛化能力评估

        Args:
            train_metrics: 训练集指标
            test_metrics: 测试集指标

        Returns:
            泛化评估结果
        """
        auc_decay = train_metrics.get('auc', 0) - test_metrics.get('auc', 0)
        return {
            'train_auc': train_metrics.get('auc', 0),
            'test_auc': test_metrics.get('auc', 0),
            'auc_decay': auc_decay,
            'overfit_risk': auc_decay > 0.1,  # AUC衰减>0.1认为过拟合
        }