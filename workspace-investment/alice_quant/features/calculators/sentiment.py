"""情绪/ML因子计算器

整合MXSearch舆情和ML模型预测概率。

因子列表：
  - mx_sentiment: MXSearch舆情评分 (0~10)
  - ml_prob_lgb: LightGBM预测概率 (0~1)
  - ml_prob_mstnn: MSTNN预测概率 (0~1)

数据来源：
  - MXSearch: scripts/mx_signal_loader.py (本地文件)
  - ML: quant_ml/data/models/ 下的模型文件
"""
import json
import os
import pickle
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List

WORK_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class SentimentFactors:
    """情绪/ML因子计算器"""

    # 缓存
    _mx_signals: Optional[dict] = None
    _ml_prob_lgb: Optional[dict] = None
    _ml_prob_mstnn: Optional[dict] = None

    @staticmethod
    def _load_mx_signals() -> dict:
        """加载MXSearch舆情信号"""
        if SentimentFactors._mx_signals is not None:
            return SentimentFactors._mx_signals

        path = os.path.join(WORK_DIR, 'data', 'mx_signals_latest.json')
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 转换为 {code: signal} 格式
            if isinstance(data, list):
                signals = {}
                for item in data:
                    code = item.get('code', '')
                    if code:
                        signals[code] = item
                SentimentFactors._mx_signals = signals
            else:
                SentimentFactors._mx_signals = data
        except Exception:
            SentimentFactors._mx_signals = {}
        return SentimentFactors._mx_signals

    @staticmethod
    def _load_ml_prob_lgb() -> dict:
        """加载LightGBM预测概率"""
        if SentimentFactors._ml_prob_lgb is not None:
            return SentimentFactors._ml_prob_lgb

        path = os.path.join(WORK_DIR, 'quant_ml', 'data', 'models', 'lgb_latest_prob.pkl')
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            if isinstance(data, dict):
                SentimentFactors._ml_prob_lgb = data
            else:
                SentimentFactors._ml_prob_lgb = {}
        except Exception:
            SentimentFactors._ml_prob_lgb = {}
        return SentimentFactors._ml_prob_lgb

    @staticmethod
    def _load_ml_prob_mstnn() -> dict:
        """加载MSTNN预测概率"""
        if SentimentFactors._ml_prob_mstnn is not None:
            return SentimentFactors._ml_prob_mstnn

        path = os.path.join(WORK_DIR, 'scripts', 'mstnn_latest_prob.pkl')
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            if isinstance(data, dict):
                SentimentFactors._ml_prob_mstnn = data
            elif isinstance(data, (list, np.ndarray)):
                # 假设是序列格式，需要code映射
                SentimentFactors._ml_prob_mstnn = {}
            else:
                SentimentFactors._ml_prob_mstnn = {}
        except Exception:
            SentimentFactors._ml_prob_mstnn = {}
        return SentimentFactors._ml_prob_mstnn

    @staticmethod
    def _normalize_code(code: str) -> str:
        """统一code格式"""
        return code.replace('sh.', '').replace('sz.', '').replace('bj.', '')

    @staticmethod
    def mx_sentiment(code: str, df: pd.DataFrame = None) -> float:
        """MXSearch舆情评分 (0~10)"""
        signals = SentimentFactors._load_mx_signals()
        clean = SentimentFactors._normalize_code(code)

        # 尝试多种code格式匹配
        for key in [code, clean, 'sh.' + clean, 'sz.' + clean]:
            sig = signals.get(key)
            if sig:
                return float(sig.get('mx_sentiment_score', 0))
        return 0.0

    @staticmethod
    def ml_prob_lgb(code: str, df: pd.DataFrame = None) -> float:
        """LightGBM预测概率 (0~1)"""
        probs = SentimentFactors._load_ml_prob_lgb()
        clean = SentimentFactors._normalize_code(code)

        for key in [code, clean, 'sh.' + clean, 'sz.' + clean]:
            prob = probs.get(key)
            if prob is not None:
                return float(prob)
        return 0.5  # 无信号时返回中性

    @staticmethod
    def ml_prob_mstnn(code: str, df: pd.DataFrame = None) -> float:
        """MSTNN预测概率 (0~1)"""
        probs = SentimentFactors._load_ml_prob_mstnn()
        clean = SentimentFactors._normalize_code(code)

        for key in [code, clean, 'sh.' + clean, 'sz.' + clean]:
            prob = probs.get(key)
            if prob is not None:
                return float(prob)
        return 0.5

    @staticmethod
    def clear_cache():
        """清空缓存"""
        SentimentFactors._mx_signals = None
        SentimentFactors._ml_prob_lgb = None
        SentimentFactors._ml_prob_mstnn = None