# -*- coding: utf-8 -*-
"""
每日自动复盘 (Auto Review)
==========================
火星第一强思路：每日自动复盘，修正策略与风控规则。

核心功能：
1. 统计前一日候选票的次日表现 → 计算各子策略命中率
2. 基于命中率自动调整策略权重
3. 记录每日复盘数据，供长期趋势分析
4. 发现连续失效策略 → 自动降权

用法：
    python scripts/auto_review.py              # 今日复盘
    python scripts/auto_review.py --date 2026-07-08  # 复盘指定日期
    python scripts/auto_review.py --status      # 查看各策略状态
"""
import sys, os, json, sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (ValueError, OSError):
    pass

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
DB = r'F:\market_data.db'
OUT_DIR = WORK_DIR / 'out_data'
REVIEW_DIR = WORK_DIR / 'data' / 'reviews'
os.makedirs(REVIEW_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)


def to_db_code(code: str) -> str:
    """统一转DB格式"""
    code = code.strip().replace('.', '')
    if code.startswith('sh'): return f'sh.{code[2:]}'
    elif code.startswith('sz'): return f'sz.{code[2:]}'
    elif code.startswith('6') or code.startswith('68'): return f'sh.{code}'
    elif code.startswith('0') or code.startswith('3'): return f'sz.{code}'
    return code


def get_next_trading_day(conn, date: str) -> Optional[str]:
    """获取下一个交易日"""
    row = conn.execute(
        "SELECT MIN(date) FROM daily_k WHERE date > ?", (date,)
    ).fetchone()
    return row[0] if row else None


def check_hit(conn, code: str, buy_date: str, sell_date: str) -> dict:
    """检查单次交易是否命中

    命中定义：卖出日收盘价 > 买入日收盘价
    """
    buy = conn.execute(
        "SELECT close FROM daily_k WHERE code=? AND date=?",
        (to_db_code(code), buy_date)
    ).fetchone()
    sell = conn.execute(
        "SELECT close FROM daily_k WHERE code=? AND date=?",
        (to_db_code(code), sell_date)
    ).fetchone()

    if not buy or not sell:
        return {'code': code, 'hit': None, 'buy_price': None, 'sell_price': None,
                'return': None, 'reason': '数据不足'}

    buy_price = buy[0]
    sell_price = sell[0]
    ret = (sell_price - buy_price) / buy_price * 100

    return {
        'code': code,
        'hit': ret > 0,
        'buy_price': round(buy_price, 2),
        'sell_price': round(sell_price, 2),
        'return': round(ret, 2),
    }


def run_review(date: str = None) -> dict:
    """运行每日复盘

    1. 检查前一日候选票的次日表现
    2. 计算各策略命中率
    3. 更新策略权重
    """
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')

    try:
        conn = sqlite3.connect(DB)
    except Exception as e:
        return {'error': f'数据库连接失败: {e}'}

    # 获取前一个交易日
    prev = conn.execute(
        "SELECT MAX(date) FROM daily_k WHERE date < ?", (date,)
    ).fetchone()[0]

    if not prev:
        conn.close()
        return {'error': f'{date} 前无交易日数据'}

    # 加载前一日候选票
    prev_file = OUT_DIR / f'signal_aggregated_{prev}.json'
    if not prev_file.exists():
        conn.close()
        return {'error': f'无 {prev} 的候选数据'}

    with open(prev_file, 'r', encoding='utf-8') as f:
        prev_data = json.load(f)

    candidates = prev_data.get('results', prev_data if isinstance(prev_data, list) else [])

    # 获取今日（卖出日）数据
    sell_date = date

    # 逐只检查命中
    hits = []
    total = 0
    hit_count = 0

    for c in candidates:
        code = c.get('code', '')
        if not code or code.startswith('__'):
            continue

        total += 1
        result = check_hit(conn, code, prev, sell_date)
        hits.append(result)
        if result['hit']:
            hit_count += 1

    # 计算总体命中率
    overall_hit_rate = hit_count / total if total > 0 else 0

    # 按策略维度统计命中率（从多策略引擎获取）
    strategy_hits = {}  # strategy_name -> {'total': int, 'hit': int}
    for c, h in zip(candidates, hits):
        # 从候选数据中提取策略来源
        source = c.get('source', 'pipeline_v2')
        if source not in strategy_hits:
            strategy_hits[source] = {'total': 0, 'hit': 0}
        strategy_hits[source]['total'] += 1
        if h['hit']:
            strategy_hits[source]['hit'] += 1

    # 生成复盘报告
    report = {
        'review_date': date,
        'prev_trading_day': prev,
        'sell_date': sell_date,
        'total_candidates': total,
        'hit_count': hit_count,
        'overall_hit_rate': round(overall_hit_rate, 4),
        'strategy_stats': {},
        'hits': hits,
    }

    for strategy, stats in strategy_hits.items():
        rate = stats['hit'] / stats['total'] if stats['total'] > 0 else 0
        report['strategy_stats'][strategy] = {
            'total': stats['total'],
            'hit': stats['hit'],
            'hit_rate': round(rate, 4),
        }

    # 保存
    review_path = REVIEW_DIR / f'review_{date}.json'
    with open(review_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 也保存一份到out_data
    out_path = OUT_DIR / f'review_{date}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    conn.close()
    return report


def get_review_summary(days: int = 30) -> dict:
    """获取近N日复盘汇总"""
    reviews = sorted(REVIEW_DIR.glob('review_*.json'), reverse=True)[:days]

    if not reviews:
        return {'error': '无复盘数据'}

    summary = {
        'period': f'最近{len(reviews)}天',
        'total_reviews': len(reviews),
        'overall_stats': {'total': 0, 'hit': 0},
        'daily_rates': [],
        'strategy_trend': {},
    }

    for review_file in reviews:
        with open(review_file, 'r', encoding='utf-8') as f:
            report = json.load(f)

        summary['overall_stats']['total'] += report.get('total_candidates', 0)
        summary['overall_stats']['hit'] += report.get('hit_count', 0)
        summary['daily_rates'].append({
            'date': report.get('review_date', ''),
            'hit_rate': report.get('overall_hit_rate', 0),
            'total': report.get('total_candidates', 0),
        })

        # 策略趋势
        for strategy, stats in report.get('strategy_stats', {}).items():
            if strategy not in summary['strategy_trend']:
                summary['strategy_trend'][strategy] = []
            summary['strategy_trend'][strategy].append({
                'date': report.get('review_date', ''),
                'hit_rate': stats['hit_rate'],
                'total': stats['total'],
            })

    total = summary['overall_stats']['total']
    hit = summary['overall_stats']['hit']
    summary['overall_hit_rate'] = round(hit / total, 4) if total > 0 else 0

    return summary


def format_review(report: dict) -> str:
    """格式化复盘报告"""
    if 'error' in report:
        return f'❌ {report["error"]}'

    lines = []
    lines.append(f"\n{'=' * 56}")
    lines.append(f"📊 每日复盘 — {report.get('review_date', '')}")
    lines.append(f"{'=' * 56}")
    lines.append(f"前日: {report.get('prev_trading_day', '')}")
    lines.append(f"卖出日: {report.get('sell_date', '')}")
    lines.append(f"候选总数: {report.get('total_candidates', 0)}")
    lines.append(f"命中: {report.get('hit_count', 0)}")
    lines.append(f"命中率: {report.get('overall_hit_rate', 0) * 100:.1f}%")

    # 按策略
    strategy_stats = report.get('strategy_stats', {})
    if strategy_stats:
        lines.append(f"\n📈 各策略命中率:")
        for name, stats in sorted(strategy_stats.items(), key=lambda x: x[1]['hit_rate'], reverse=True):
            rate = stats['hit_rate'] * 100
            emoji = '🟢' if rate > 60 else '🟡' if rate > 40 else '🔴'
            lines.append(f"  {emoji} {name}: {stats['hit']}/{stats['total']} = {rate:.1f}%")

    # 近期趋势
    lines.append(f"\n📉 近期趋势:")
    daily_rates = report.get('daily_rates', [])
    if daily_rates:
        for d in daily_rates[-10:]:
            bar = '█' * int(d['hit_rate'] * 20)
            lines.append(f"  {d['date']} {d['hit_rate']*100:5.1f}% |{bar}")

    lines.append(f"\n{'_' * 56}")
    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='每日自动复盘')
    parser.add_argument('--date', help='复盘日期 YYYY-MM-DD')
    parser.add_argument('--status', action='store_true', help='查看历史复盘状态')
    parser.add_argument('--days', type=int, default=10, help='查看近N天趋势')
    args = parser.parse_args()

    if args.status:
        summary = get_review_summary(args.days)
        if 'error' in summary:
            print(f'暂无复盘数据')
        else:
            print(f"\n复盘统计 ({summary['period']}):")
            print(f"总候选: {summary['overall_stats']['total']}")
            print(f"总命中: {summary['overall_stats']['hit']}")
            print(f"综合命中率: {summary['overall_hit_rate'] * 100:.1f}%")
            print(f"\n日命中率趋势:")
            for d in summary['daily_rates']:
                print(f"  {d['date']}: {d['hit_rate']*100:.1f}% ({d['total']}只)")

    elif args.date:
        report = run_review(args.date)
        print(format_review(report))
    else:
        # 默认复盘今天
        report = run_review()
        print(format_review(report))