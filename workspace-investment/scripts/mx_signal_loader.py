# -*- coding: utf-8 -*-
"""
MXSearch舆情信号加载器
把每日舆情信号（stats.json）转换为评分因子，供多因子评分使用

数据源:
  logs/mx_search_daily/stats.json  - 历史信号+收益
  logs/mx_search_daily/today.json  - 今日采集信号

输出:
  scripts/mx_signals_latest.json    - 供多因子评分读取
"""
import io
import sys, json, os
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
LOG_DIR = os.path.join(WORK_DIR, 'logs', 'mx_search_daily')
STATS_FILE = os.path.join(LOG_DIR, 'stats.json')
TODAY_FILE = os.path.join(LOG_DIR, 'today.json')
OUTPUT_FILE = os.path.join(WORK_DIR, 'scripts', 'mx_signals_latest.json')


def load_stats():
    """加载历史信号+收益"""
    if not os.path.exists(STATS_FILE):
        return []
    try:
        with open(STATS_FILE, encoding='utf-8') as f:
            d = json.load(f)
        return d.get('records', [])
    except:
        return []


def load_today():
    """加载今日采集信号"""
    if not os.path.exists(TODAY_FILE):
        return []
    try:
        with open(TODAY_FILE, encoding='utf-8') as f:
            d = json.load(f)
        return d.get('records', [])
    except:
        return []


def compute_signal_stats(records):
    """从历史数据中找出有效信号模式"""
    # 只用有T+1收益的记录
    valid = [r for r in records if r.get('next_return') is not None]
    if not valid:
        return {}

    # 按score分组统计
    score_groups = {}
    for r in valid:
        s = r.get('score', 0)
        if s not in score_groups:
            score_groups[s] = {'returns': [], 'count': 0}
        score_groups[s]['returns'].append(r['next_return'])
        score_groups[s]['count'] += 1

    # 计算每个score等级的平均收益和胜率
    stats = {}
    for score, group in score_groups.items():
        rets = group['returns']
        avg = sum(rets) / len(rets)
        win_rate = sum(1 for x in rets if x > 0) / len(rets)
        stats[score] = {
            'avg_return': round(avg, 4),
            'win_rate': round(win_rate, 4),
            'count': group['count']
        }

    # 找最优score阈值
    best_score = max(stats.keys(), key=lambda s: stats[s]['avg_return'])
    return {
        'stats_by_score': stats,
        'best_score': best_score,
        'best_avg_return': stats[best_score]['avg_return'],
        'best_win_rate': stats[best_score]['win_rate'],
        'total_valid': len(valid)
    }


def get_code_signal(code, today_records, cutoff_days=7):
    """获取个股近N日最新舆情信号"""
    cutoff = (datetime.now() - timedelta(days=cutoff_days)).strftime('%Y-%m-%d')
    matches = []
    for r in today_records:
        if r.get('code') == code and r.get('date', '') >= cutoff:
            matches.append(r)

    if not matches:
        return None

    # 选最新且得分最高的
    best = max(matches, key=lambda x: x.get('score', 0))
    return {
        'code': code,
        'name': best.get('name', ''),
        'title': best.get('title', '')[:60],
        'date': best.get('date', ''),
        'score': best.get('score', 0),
        'has_positive': best.get('has_positive', False),
        'has_negative': best.get('has_negative', False),
        'keywords': best.get('keywords', {}),
    }


def sentiment_to_score(signal, signal_stats):
    """把舆情信号转换为评分(0-10)"""
    if signal is None:
        return 0

    score = signal.get('score', 0)

    # 分数档位
    if score >= 3:
        base = 10
    elif score == 2:
        base = 7
    elif score == 1:
        base = 4
    else:
        base = 0

    # 有正面关键词加权
    if signal.get('has_positive'):
        bonus = 0
        pos_kw = signal.get('keywords', {}).get('positive', [])
        if any(kw in ['增长', '超预期', '回购', '增持', '评级上调', '业绩', '订单', '量产']
               for kw in pos_kw):
            bonus = 2
        elif pos_kw:
            bonus = 1
        base = min(10, base + bonus)

    # 有负面关键词扣分
    if signal.get('has_negative'):
        neg_kw = signal.get('keywords', {}).get('negative', [])
        if any(kw in ['减持', '调查', '处罚', 'ST', '亏损', '违约']
               for kw in neg_kw):
            base = max(0, base - 4)

    return base


def generate_signal_report(today_records):
    """生成信号报告"""
    # 找出所有有正面信号的股票
    positive = [r for r in today_records
                if r.get('has_positive') and r.get('score', 0) >= 1]
    negative = [r for r in today_records
                if r.get('has_negative') and r.get('score', 0) <= -1]

    # 按score排序
    positive.sort(key=lambda x: x.get('score', 0), reverse=True)
    negative.sort(key=lambda x: x.get('score', 0))

    return {
        'positive_signals': [{
            'code': r['code'], 'name': r['name'],
            'title': r.get('title', '')[:40],
            'score': r.get('score', 0),
            'keywords': r.get('keywords', {}).get('positive', [])[:5]
        } for r in positive[:10]],
        'negative_signals': [{
            'code': r['code'], 'name': r['name'],
            'title': r.get('title', '')[:40],
            'score': r.get('score', 0),
            'keywords': r.get('keywords', {}).get('negative', [])[:5]
        } for r in negative[:5]],
    }


def main():
    today_records = load_today()
    all_records = load_stats()
    signal_stats = compute_signal_stats(all_records)

    # 生成个股舆情评分
    all_codes = set(r['code'] for r in today_records if r.get('code'))
    signals = {}
    for code in all_codes:
        sig = get_code_signal(code, today_records)
        if sig:
            mx_score = sentiment_to_score(sig, signal_stats)
            sig['mx_sentiment_score'] = mx_score
            signals[code] = sig

    output = {
        'generated_at': datetime.now().isoformat(),
        'signal_stats': signal_stats,
        'today_count': len(today_records),
        'total_history': len(all_records),
        'signals': signals,
        'report': generate_signal_report(today_records),
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[MXSearch信号加载器]")
    print(f"  今日信号: {len(today_records)}条")
    print(f"  历史有效样本: {signal_stats.get('total_valid', 0)}条")
    if signal_stats:
        print(f"  最优score={signal_stats['best_score']}, "
              f"平均收益={signal_stats['best_avg_return']:+.3f}%, "
              f"胜率={signal_stats['best_win_rate']:.1%}")
    print(f"  有效舆情股票: {len(signals)}只")
    print(f"  输出: {OUTPUT_FILE}")

    # 正面信号摘要
    report = output['report']
    if report['positive_signals']:
        print(f"\n  正面信号 TOP5:")
        for s in report['positive_signals'][:5]:
            print(f"    {s['name']}({s['code']}) score={s['score']} "
                  f"{' '.join(s['keywords'][:3])}")
    if report['negative_signals']:
        print(f"\n  负面信号:")
        for s in report['negative_signals'][:3]:
            print(f"    {s['name']}({s['code']}) score={s['score']} "
                  f"{' '.join(s['keywords'][:3])}")

    return output


def get_mx_sentiment(code):
    """供 multi_factor_scoring.py 调用，传入股票代码返回舆情信号"""
    OUTPUT_FILE_LOCAL = os.path.join(
        r'C:\Users\Administrator\.openclaw\workspace\workspace-investment',
        'scripts', 'mx_signals_latest.json'
    )
    if not os.path.exists(OUTPUT_FILE_LOCAL):
        return None
    try:
        with open(OUTPUT_FILE_LOCAL, encoding='utf-8') as f:
            d = json.load(f)
        return d.get('signals', {}).get(code)
    except:
        return None


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
