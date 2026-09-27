# -*- coding: utf-8 -*-
"""
ML因子加载器 v2 — 集成LightGBM + MSTNN双模型

用法:
    from ml_factor_loader import get_ml_factor, get_ml_prob
    prob = get_ml_prob('600000')     # 综合概率（双模型融合）
    score = get_ml_factor('600000')  # 0~10分
"""
import os, json, pickle, warnings
from pathlib import Path
import numpy as np

warnings.filterwarnings('ignore')

# 缓存路径
LGBM_PROB_CACHE = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts\ml_latest_prob.pkl')
MSTNN_PROB_CACHE = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts\mstnn_latest_prob.pkl')

_lgbm_cache = None
_mstnn_cache = None


def load_latest_probabilities():
    """加载LightGBM预测概率"""
    global _lgbm_cache
    if _lgbm_cache is not None:
        return _lgbm_cache
    if not LGBM_PROB_CACHE.exists():
        _lgbm_cache = {}
        return {}
    try:
        with open(LGBM_PROB_CACHE, 'rb') as f:
            data = pickle.load(f)
        _lgbm_cache = data if isinstance(data, dict) else {}
    except Exception:
        _lgbm_cache = {}
    return _lgbm_cache


def load_mstnn_probabilities():
    """加载MSTNN预测概率"""
    global _mstnn_cache
    if _mstnn_cache is not None:
        return _mstnn_cache
    if not MSTNN_PROB_CACHE.exists():
        _mstnn_cache = {}
        return {}
    try:
        with open(MSTNN_PROB_CACHE, 'rb') as f:
            data = pickle.load(f)
        _mstnn_cache = data if isinstance(data, dict) else {}
    except Exception:
        _mstnn_cache = {}
    return _mstnn_cache


def _normalize_code(code: str) -> str:
    """去掉sz/sh/bj前缀及点号"""
    code = str(code).strip()
    for prefix in ('sz.', 'sh.', 'bj.', 'sz', 'sh', 'bj'):
        if code.lower().startswith(prefix):
            code = code[len(prefix):]
            break
    return code


def get_ml_prob(code: str, fusion: str = 'avg') -> float:
    """
    获取综合ML上涨概率（双模型融合）
    fusion: 'avg'=等权平均, 'max'=取高值, 'lgbm_only'=仅LightGBM, 'mstnn_only'=仅MSTNN
    """
    code = _normalize_code(code)

    lgbm_probs = load_latest_probabilities()
    mstnn_probs = load_mstnn_probabilities()

    # LightGBM: 先查纯数字，再查带前缀的key（unified_train保存的key带sh./sz.前缀）
    p_lgbm = lgbm_probs.get(code, None)
    if p_lgbm is None:
        # 尝试带前缀
        for prefix in ['sh.', 'sz.', 'bj.']:
            key = prefix + code
            if key in lgbm_probs:
                p_lgbm = lgbm_probs[key]
                break
    if p_lgbm is None:
        # 反过来：如果lgbm的key是纯数字，但code可能之前被normalize过
        for k, v in lgbm_probs.items():
            if k.replace('sh.','').replace('sz.','').replace('bj.','') == code:
                p_lgbm = v
                break

    # MSTNN: key可能是纯数字或带前缀（sh.xxx / sz.xxx）
    p_mstnn = mstnn_probs.get(code, None)
    if p_mstnn is None:
        # 尝试带前缀
        for prefix in ['sh.', 'sz.', 'bj.']:
            key = prefix + code
            if key in mstnn_probs:
                p_mstnn = mstnn_probs[key]
                break
    if p_mstnn is None:
        # 反过来：如果mstnn的key是纯数字，code可能是带前缀的
        for k, v in mstnn_probs.items():
            if k.replace('sh.','').replace('sz.','').replace('bj.','') == code:
                p_mstnn = v
                break

    # 只有单一模型有数据时
    if p_lgbm is None and p_mstnn is None:
        return None
    if p_lgbm is None:
        return float(p_mstnn)
    if p_mstnn is None:
        return float(p_lgbm)

    # 双模型融合
    if fusion == 'max':
        return float(max(p_lgbm, p_mstnn))
    elif fusion == 'lgbm_only':
        return float(p_lgbm)
    elif fusion == 'mstnn_only':
        return float(p_mstnn)
    else:  # avg
        return float((p_lgbm + p_mstnn) / 2.0)


_calib_cache = None

def _load_calibration():
    """加载概率校准数据（百分位数→分布）"""
    global _calib_cache
    if _calib_cache is not None:
        return _calib_cache
    try:
        probs = load_latest_probabilities()
        if not probs:
            _calib_cache = {'percentiles': []}
            return _calib_cache
        import numpy as np
        vs = np.array(sorted(probs.values()))
        _calib_cache = {
            'percentiles': vs.tolist(),  # 完整的概率分布，用于百分位计算
        }
        return _calib_cache
    except:
        _calib_cache = {'percentiles': []}
        return _calib_cache


def prob_to_score(prob: float, max_score: float = 10.0) -> float:
    """
    概率转评分 (0~10分)
    直接用全市场百分位排名，不管概率绝对值：
    Top 10% → 10分
    Top 20% → 8分
    Top 50% → 4分
    后50% → 0分
    """
    if prob is None or prob <= 0:
        return 0.0
    
    cal = _load_calibration()
    percentiles = cal.get('percentiles', [])
    
    if not percentiles:
        return 0.0
    
    import numpy as np
    sorted_vals = np.array(percentiles)
    n = len(sorted_vals)
    
    # 计算百分位排名（0~1）
    rank_pct = float(np.searchsorted(sorted_vals, prob)) / n
    
    # 后50% → 0分
    if rank_pct < 0.50:
        return 0.0
    
    # 前50%：0.50~1.00 → 0~10分
    # 用平方使高分更稀缺（Top10%→10分，Top50%→4分）
    raw = (rank_pct - 0.50) / 0.50
    score = raw * raw * max_score
    return round(min(max_score, score), 1)


def get_ml_factor(code: str, fusion: str = 'avg') -> float:
    """获取单只股票ML因子评分 (0~10分)"""
    prob = get_ml_prob(code, fusion=fusion)
    return prob_to_score(prob)


def invalidate_cache():
    """手动刷新缓存"""
    global _lgbm_cache, _mstnn_cache
    _lgbm_cache = None
    _mstnn_cache = None


def get_model_stats() -> dict:
    """返回双模型状态统计"""
    lgbm = load_latest_probabilities()
    mstnn = load_mstnn_probabilities()

    stats = {
        'lgbm': {'count': len(lgbm), 'available': len(lgbm) > 0},
        'mstnn': {'count': len(mstnn), 'available': len(mstnn) > 0},
    }

    # 交集
    common = set(lgbm.keys()) & set(mstnn.keys())
    stats['fusion'] = {
        'common_count': len(common),
        'fusion_available': len(lgbm) > 0 and len(mstnn) > 0,
    }

    # 统计分布
    for name, probs in [('lgbm', lgbm), ('mstnn', mstnn)]:
        if probs:
            vals = np.array(sorted(probs.values()))
            stats[name]['percentiles'] = {
                'p10': round(float(np.percentile(vals, 10)), 4),
                'p25': round(float(np.percentile(vals, 25)), 4),
                'p50': round(float(np.percentile(vals, 50)), 4),
                'p75': round(float(np.percentile(vals, 75)), 4),
                'p90': round(float(np.percentile(vals, 90)), 4),
                'p95': round(float(np.percentile(vals, 95)), 4),
                'p99': round(float(np.percentile(vals, 99)), 4),
                'min': round(float(np.min(vals)), 4),
                'max': round(float(np.max(vals)), 4),
            }

    return stats


if __name__ == '__main__':
    print("=" * 50)
    print("ML因子加载器 v2 - 测试")
    print("=" * 50)
    stats = get_model_stats()
    print(f"LightGBM: {stats['lgbm']['count']}只")
    if 'percentiles' in stats['lgbm']:
        pc = stats['lgbm']['percentiles']
        print(f"  分布: min={pc['min']} p10={pc['p10']} p50={pc['p50']} p90={pc['p90']} p99={pc['p99']} max={pc['max']}")
        print(f"  校准: Top10%概率阈值={pc['p90']:.4f}, Top5%={pc['p95']:.4f}")
    print(f"MSTNN: {stats['mstnn']['count']}只")
    if 'percentiles' in stats['mstnn']:
        pc = stats['mstnn']['percentiles']
        print(f"  分布: min={pc['min']} p50={pc['p50']} p90={pc['p90']} max={pc['max']}")
    print(f"交集: {stats['fusion']['common_count']}只")

    # 测试几个代码
    for code in ['600000', '000858', '002805', '600519']:
        p = get_ml_prob(code)
        s = get_ml_factor(code)
        if p:
            print(f"  {code}: P={p:.3f} 评分={s}")
        else:
            print(f"  {code}: 无数据")