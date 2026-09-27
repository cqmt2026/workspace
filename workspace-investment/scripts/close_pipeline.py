# -*- coding: utf-8 -*-
"""
收盘后全链路执行脚本
=====================
整合前置过滤 + 多策略引擎 + 信号聚合 + 复盘

每天收盘后调用一次，完成所有选股链路的闭环。

用法：
    python scripts/close_pipeline.py                    # 今天
    python scripts/close_pipeline.py 2026-07-09         # 指定日期
"""
import io
import sys, os, json, sqlite3
from datetime import datetime
from pathlib import Path

# sys.stdout.reconfigure will be called after module load check at bottom

def _safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        pass

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
DB = r'F:\market_data.db'
OUT_DIR = WORK_DIR / 'out_data'
os.makedirs(OUT_DIR, exist_ok=True)


def load_factors(date: str):
    """从factors.db加载当日所有因子数据"""
    fdb = WORK_DIR / 'data' / 'factors.db'
    if not fdb.exists():
        return {}
    conn = sqlite3.connect(str(fdb))
    rows = conn.execute(
        "SELECT code, factor_name, value FROM factors WHERE date=?",
        (date,)
    ).fetchall()
    conn.close()
    factors = {}
    for code, fname, val in rows:
        if code not in factors:
            factors[code] = {}
        factors[code][fname] = val
    return factors


def run_prefilter(date: str, factors: dict) -> dict:
    """运行前置过滤，返回过滤统计"""
    sys.path.insert(0, str(WORK_DIR))
    from alice_quant.strategies.pre_filter import PreFilter

    # 创建一个模拟的feature_engine对象
    class MockFeature:
        def get_factor(self, code, name, date):
            f = factors.get(code, {})
            return f.get(name)

    pf = PreFilter(feature_engine=MockFeature())

    # 构造候选列表
    candidates = []
    for code, f in factors.items():
        price = f.get('ma_5', f.get('ma_20', 0))
        if price > 0:
            candidates.append({'code': code, 'price': price})

    result = pf.filter(candidates, date)
    stats = pf.get_stats()

    # 保存
    output = {
        'date': date,
        'stats': stats,
        'passed_codes': [c['code'] for c in result.passed],
        'eliminated_codes': {c['code']: c.get('elimination_reason', '') for c in result.eliminated},
    }
    path = OUT_DIR / f'prefilter_{date}.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'  前置过滤: 通过{stats["passed"]}只, 淘汰{stats["eliminated"]}只')
    return output


def run_multi_strategy(date: str, factors: dict, passed_codes: list) -> dict:
    """运行多策略引擎，返回投票结果"""
    sys.path.insert(0, str(WORK_DIR))
    from alice_quant.strategies.multi_strategy import MultiStrategyEngine

    # Mock feature
    class MockFeature:
        def get_factor(self, code, name, date):
            f = factors.get(code, {})
            return f.get(name)

    engine = MultiStrategyEngine(feature_engine=MockFeature())

    candidates = []
    for code in passed_codes:
        price = factors.get(code, {}).get('ma_5', 0)
        if price > 0:
            candidates.append({'code': code, 'price': price})

    results = engine.evaluate(candidates, date, top_n=10, min_consensus=1)

    output = {
        'date': date,
        'results': [{
            'code': r.code,
            'final_score': r.final_score,
            'consensus': r.consensus,
            'avg_score': r.avg_score,
            'selected': r.selected,
            'votes': [{'strategy': v.strategy_name, 'score': v.score, 'weight': v.weight} for v in r.votes],
        } for r in results],
    }
    path = OUT_DIR / f'multi_strategy_{date}.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'  多策略引擎: {len(results)}只有投票')
    return output


def run_auto_review(date: str):
    """运行自动复盘"""
    sys.path.insert(0, str(WORK_DIR / 'scripts'))
    import auto_review
    report = auto_review.run_review(date)
    if 'error' in report:
        print(f'  复盘: {report["error"]}')
    else:
        print(f'  复盘: 命中率{report.get("overall_hit_rate",0)*100:.1f}%')
    return report


def run_signal_aggregator(date: str):
    """运行信号聚合器"""
    sys.path.insert(0, str(WORK_DIR / 'scripts'))
    from signal_aggregator import SignalAggregator
    agg = SignalAggregator()
    results = agg.aggregate(date)
    agg.close()
    _safe_print(f'  信号聚合: {len(results)}只候选')
    return results


def main():
    # 解析参数：支持 python close_pipeline.py 2026-07-10 或 python close_pipeline.py --date 2026-07-10
    args = sys.argv[1:]
    date = None
    
    # 先找 --date 参数
    for i, a in enumerate(args):
        if a == '--date' and i + 1 < len(args):
            date = args[i + 1]
            break
    
    # 没找到 --date，找第一个非--开头的参数
    if date is None:
        for a in args:
            if not a.startswith('--'):
                date = a
                break
    
    # 都没找到，用今天
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # 防御：确保date是合理的日期格式，不是 '--date' 本身
    if date == '--date':
        date = datetime.now().strftime('%Y-%m-%d')

    _safe_print(f'\n{"=" * 56}')
    _safe_print(f'收盘全链路执行 — {date}')
    _safe_print(f'{"=" * 56}')

    # 1. 加载因子数据
    _safe_print('\n1. 加载因子数据...')
    factors = load_factors(date)
    _safe_print(f'   因子数据: {len(factors)}只有因子')

    # 2. 前置过滤
    _safe_print('\n2. 前置过滤...')
    pf_result = run_prefilter(date, factors)

    # 3. 多策略引擎
    _safe_print('\n3. 多策略引擎...')
    ms_result = run_multi_strategy(date, factors, pf_result['passed_codes'])

    # 4. 信号聚合（已包含多策略和形态雷达）
    _safe_print('\n4. 信号聚合...')
    sig_result = run_signal_aggregator(date)

    # 5. 自动复盘（检查前一日命中率）
    try:
        _safe_print('\n5. 自动复盘...')
        review_result = run_auto_review(date)
    except Exception as e:
        _safe_print(f'  复盘跳过: {e}')

    _safe_print(f'\n{"=" * 56}')
    _safe_print(f'全链路完成！')
    _safe_print(f'{"=" * 56}')


# Reconfigure stdout after all module imports
if __name__ == '__main__' and sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except (ValueError, OSError):
        pass

if __name__ == '__main__':
    main()