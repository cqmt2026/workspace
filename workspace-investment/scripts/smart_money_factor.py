# -*- coding: utf-8 -*-
"""
SmartMoney 资金因子扫描脚本
===========================
对指定股票池计算资金流因子（强度/持续性/价量确认/冲击效率/综合评分），
输出 Top N 排名结果，同时记录评分明细到日志。

用法:
  python scripts/smart_money_factor.py --codes sz.300750 sh.600519 ... --topn 10
  python scripts/smart_money_factor.py --pool config/stock_pool.json --topn 10
  python scripts/smart_money_factor.py --pool config/stock_pool.json --topn 10 --verbose
"""
import io
import sys
import os
import json
import time
import argparse
from datetime import datetime
from typing import List, Tuple, Optional, Dict

# 立即刷新输出
import builtins as _builtins
def print(*a, **kw):
    kw.pop('flush', None)  # 移除可能冲突的flush参数
    _builtins.print(*a, **kw, flush=True)

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORK_DIR)

from alice_quant.features.calculators.money_flow import MoneyFlowFactors


def load_stock_pool(pool_path: str) -> List[str]:
    """从 stock_pool.json 加载股票代码列表"""
    with open(pool_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    codes = []
    for s in data.get('stocks', []):
        code = s.get('code', '')
        if code:
            codes.append(code)
    return codes


def compute_single(code: str) -> Dict:
    """计算单只股票的所有资金因子"""
    mf = MoneyFlowFactors()
    result = {
        'code': code,
        'flow_intensity': mf.flow_intensity(code),
        'flow_persistence': mf.flow_persistence(code),
        'price_confirmation': mf.price_confirmation(code),
        'impact_efficiency': mf.impact_efficiency(code),
        'smart_money_score': mf.smart_money_score(code),
    }
    return result


def get_stock_name(code: str) -> str:
    """尝试从 stock_pool.json 获取股票名称"""
    try:
        pool_path = os.path.join(WORK_DIR, 'config', 'stock_pool.json')
        with open(pool_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        name_map = {s['code']: s.get('name', '') for s in data.get('stocks', [])}
        return name_map.get(code, '')
    except Exception:
        return ''


def main():
    parser = argparse.ArgumentParser(description='SmartMoney资金因子扫描')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--codes', nargs='+', help='股票代码列表')
    group.add_argument('--pool', type=str, help='股票池JSON文件路径')
    parser.add_argument('--topn', type=int, default=10, help='输出Top N')
    parser.add_argument('--verbose', action='store_true', help='输出所有股票的评分明细')
    parser.add_argument('--min-score', type=float, default=0.0,
                        help='最低综合评分过滤（默认0，即不过滤）')
    args = parser.parse_args()

    # 加载股票列表
    if args.pool:
        pool_path = args.pool
        if not os.path.isabs(pool_path):
            pool_path = os.path.join(WORK_DIR, pool_path)
        codes = load_stock_pool(pool_path)
        print(f"📦 从股票池加载 {len(codes)} 只股票")
    else:
        codes = args.codes
        print(f"📦 命令行指定 {len(codes)} 只股票")

    if not codes:
        print("❌ 股票列表为空，退出")
        return

    # 名称映射
    name_map = {}
    try:
        pool_path = os.path.join(WORK_DIR, 'config', 'stock_pool.json')
        with open(pool_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        name_map = {s['code']: s.get('name', '') for s in data.get('stocks', [])}
    except Exception:
        pass

    # 逐只计算
    results = []
    errors = []
    total = len(codes)

    print(f"\n{'='*60}")
    print(f"  SmartMoney 资金因子扫描 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  股票数量: {total} 只 | Top N: {args.topn}")
    print(f"{'='*60}\n")

    start_ts = time.time()

    for i, code in enumerate(codes, 1):
        try:
            name = name_map.get(code, get_stock_name(code))
            print(f"  [{i:3d}/{total}] {code} {name:>8s} ... ", end='', flush=True)
            r = compute_single(code)
            results.append(r)
            print(f"评分={r['smart_money_score']:5.1f} | "
                  f"强度={r['flow_intensity']:+.2%} | "
                  f"持续={r['flow_persistence']:.0%} | "
                  f"价量={r['price_confirmation']:.0%}")
        except Exception as e:
            errors.append((code, str(e)))
            print(f"❌ 错误: {e}")

    elapsed = time.time() - start_ts
    print(f"\n⏱ 耗时: {elapsed:.1f}s | 成功: {len(results)} | 失败: {len(errors)}")

    if errors:
        print(f"\n⚠️  失败列表 ({len(errors)}):")
        for code, err in errors:
            print(f"   {code}: {err}")

    if not results:
        print("\n❌ 无有效结果")
        return

    # 按综合评分排序
    results.sort(key=lambda x: x['smart_money_score'], reverse=True)

    # 过滤最低分
    if args.min_score > 0:
        results = [r for r in results if r['smart_money_score'] >= args.min_score]

    # 输出 Top N
    top_n = min(args.topn, len(results))
    print(f"\n{'='*60}")
    print(f"  🏆 SmartMoney Top {top_n}")
    print(f"{'='*60}")
    print(f"  {'排名':>4s} | {'代码':<14s} | {'名称':<8s} | {'综合评分':>8s} | "
          f"{'强度':>7s} | {'持续性':>6s} | {'价量确认':>7s} | {'冲击效率':>7s}")
    print(f"  {'-'*4}-+-{'-'*14}-+-{'-'*8}-+-{'-'*8}-+-"
          f"{'-'*7}-+-{'-'*6}-+-{'-'*7}-+-{'-'*7}")

    for rank, r in enumerate(results[:top_n], 1):
        name = name_map.get(r['code'], get_stock_name(r['code']))
        print(f"  {rank:4d} | {r['code']:<14s} | {name:<8s} | "
              f"{r['smart_money_score']:>7.1f} | "
              f"{r['flow_intensity']:>+6.2%} | "
              f"{r['flow_persistence']:>5.0%} | "
              f"{r['price_confirmation']:>6.0%} | "
              f"{r['impact_efficiency']:>+6.2f}")

    # 底部汇总
    avg_score = sum(r['smart_money_score'] for r in results) / len(results)
    avg_intensity = sum(r['flow_intensity'] for r in results) / len(results)
    avg_persistence = sum(r['flow_persistence'] for r in results) / len(results)
    print(f"\n📊 股票池均值:")
    print(f"   综合评分: {avg_score:.1f} | "
          f"资金强度: {avg_intensity:+.2%} | "
          f"持续性: {avg_persistence:.0%}")

    # 强势/弱势分布
    strong = sum(1 for r in results if r['smart_money_score'] >= 60)
    weak = sum(1 for r in results if r['smart_money_score'] < 20)
    print(f"   强势(>=60): {strong}只 | 弱势(<20): {weak}只")

    # 底部Top 3 推荐
    print(f"\n💡 资金面Top 3推荐:")
    for r in results[:3]:
        name = name_map.get(r['code'], get_stock_name(r['code']))
        print(f"   🥇 {r['code']} {name} — 评分{r['smart_money_score']:.1f}，"
              f"资金强度{r['flow_intensity']:+.2%}，"
              f"持续性{r['flow_persistence']:.0%}")

    print(f"\n{'='*60}")
    print(f"  扫描完成: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()