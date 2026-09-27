# -*- coding: utf-8 -*-
"""
决策复盘自动回写 Obsidian
==========================
功能：
    1. 读取本周推荐追踪数据（recommendation_tracker.json）
    2. 分析胜率/收益/失败模式
    3. 生成复盘Markdown文件，归档到 03-项目/贾维斯系统/复盘/
    4. 如果胜率低于阈值，自动建议调整策略

用法：
    python scripts/review_to_obsidian.py

Cron: 每周五17:00（已在INV-Weekly-Review-周五中触发）
"""
import io
import sys, os, json
from datetime import datetime, date, timedelta
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-investment")
OBSIDIAN_VAULT = Path(r"C:\Users\Administrator\Obsidian\Jarvis")
REVIEW_DIR = OBSIDIAN_VAULT / "03-项目" / "贾维斯系统" / "复盘"
TRACKER_FILE = WORKSPACE / "data" / "recommendation_tracker.json"
SIGNAL_FILE = WORKSPACE / "out_data" / "signal_aggregated"

def load_tracker():
    """加载推荐追踪数据"""
    if not TRACKER_FILE.exists():
        return []
    try:
        with open(TRACKER_FILE, encoding='utf-8') as f:
            data = json.load(f)
        return data.get('recommendations', data.get('records', []))
    except:
        return []

def compute_weekly_stats(records):
    """计算本周统计数据"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    this_week = [r for r in records if r.get('date', '')[:10] >= week_start.isoformat()]
    
    if not this_week:
        return None
    
    total = len(this_week)
    wins = sum(1 for r in this_week if r.get('result') == 'win' or r.get('return_pct', 0) > 0)
    losses = sum(1 for r in this_week if r.get('result') == 'loss' or r.get('return_pct', 0) <= 0)
    pending = sum(1 for r in this_week if r.get('status') == 'pending' or r.get('result') is None)
    
    returns = [r.get('return_pct', 0) for r in this_week if r.get('return_pct') is not None]
    avg_return = sum(returns) / len(returns) if returns else 0
    max_return = max(returns) if returns else 0
    min_return = min(returns) if returns else 0
    
    # 按信号源分类
    by_source = {}
    for r in this_week:
        src = r.get('source', r.get('signal_source', 'unknown'))
        if src not in by_source:
            by_source[src] = {'total': 0, 'wins': 0, 'returns': []}
        by_source[src]['total'] += 1
        if r.get('return_pct', 0) > 0:
            by_source[src]['wins'] += 1
        if r.get('return_pct') is not None:
            by_source[src]['returns'].append(r['return_pct'])
    
    return {
        'week_start': week_start.isoformat(),
        'total': total,
        'wins': wins,
        'losses': losses,
        'pending': pending,
        'win_rate': wins / total * 100 if total > 0 else 0,
        'avg_return': avg_return,
        'max_return': max_return,
        'min_return': min_return,
        'by_source': by_source,
        'records': this_week,
    }

def generate_obsidian_review(stats, today_str):
    """生成Obsidian复盘Markdown"""
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "---",
        f"tags: [复盘, 周报, 决策]",
        f"date: {today_str}",
        f"week: {stats['week_start']}",
        f"win_rate: {stats['win_rate']:.1f}%",
        "---",
        "",
        f"# 决策复盘 · {stats['week_start']} ~ {today_str}",
        "",
        "## 📊 本周总览",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 推荐总数 | {stats['total']} |",
        f"| 成功 | {stats['wins']} |",
        f"| 失败 | {stats['losses']} |",
        f"| 待确认 | {stats['pending']} |",
        f"| 胜率 | {stats['win_rate']:.1f}% |",
        f"| 平均收益 | {stats['avg_return']:+.2f}% |",
        f"| 最大收益 | {stats['max_return']:+.2f}% |",
        f"| 最小收益 | {stats['min_return']:+.2f}% |",
        "",
    ]
    
    # 信号源分析
    lines.append("## 📈 信号源表现")
    lines.append("")
    lines.append("| 信号源 | 推荐数 | 胜率 | 均收益 |")
    lines.append("|--------|--------|------|--------|")
    for src, s in sorted(stats['by_source'].items()):
        wr = s['wins'] / s['total'] * 100 if s['total'] > 0 else 0
        ar = sum(s['returns']) / len(s['returns']) if s['returns'] else 0
        status = "🟢" if wr >= 60 else "🟡" if wr >= 40 else "🔴"
        lines.append(f"| {src} | {s['total']} | {wr:.0f}% {status} | {ar:+.2f}% |")
    
    lines.extend([
        "",
        "## 💡 策略建议",
        "",
    ])
    
    # 自动建议
    if stats['win_rate'] < 40:
        lines.append("- ⚠️ 胜率低于40%，建议：")
        lines.append("  - 检查信号源质量，考虑暂停低胜率信号")
        lines.append("  - 收紧买入条件（缩量+低位双确认）")
    elif stats['win_rate'] < 55:
        lines.append("- 🟡 胜率偏低，建议：")
        lines.append("  - 回顾失败案例，寻找共同模式")
        lines.append("  - 适当降低仓位")
    elif stats['win_rate'] >= 65:
        lines.append("- ✅ 胜率良好，当前策略有效")
        lines.append("  - 保持现有参数")
    else:
        lines.append("- 🟢 胜率正常，继续执行")
    
    lines.extend([
        "",
        "---",
        "",
        "## 🔗 相关",
        "",
        "- [[推荐追踪/最新看板]]",
        "- [[策略笔记/缩量回调策略]]",
    ])
    
    md = "\n".join(lines)
    review_file = REVIEW_DIR / f"review_{today_str}.md"
    with open(review_file, 'w', encoding='utf-8') as f:
        f.write(md)
    
    # 同步到最新
    latest = REVIEW_DIR / "最新复盘.md"
    with open(latest, 'w', encoding='utf-8') as f:
        f.write(md)
    
    print(f"[Obsidian] 复盘已归档: {review_file}")
    return review_file

def main():
    print("=" * 55)
    print("决策复盘 → Obsidian")
    print("=" * 55)
    
    records = load_tracker()
    stats = compute_weekly_stats(records)
    
    if not stats:
        print("⚠️ 本周无推荐数据，跳过复盘")
        return
    
    print(f"本周推荐: {stats['total']}条, 胜率: {stats['win_rate']:.1f}%")
    today_str = date.today().isoformat()
    
    review_file = generate_obsidian_review(stats, today_str)
    print(f"✅ 复盘已归档: {review_file}")
    print(f"{'='*55}")

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    main()