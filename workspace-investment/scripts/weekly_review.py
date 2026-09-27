# -*- coding: utf-8 -*-
"""
每周推荐复盘
周五收盘后运行：
1. 统计各信号源胜率
2. 砍掉低于阈值的信号源
3. 输出本周推荐Top5和Bottom5
"""
import io
import sys, os, json
from datetime import date
sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
sys.path.insert(0, WORKSPACE)

from scripts.recommendation_tracker import init_tracker, compute_stats, save_tracker, TRACK_FILE

def main():
    print("=" * 55)
    print("每周推荐复盘")
    print("=" * 55)
    
    # 1. 更新所有追踪
    from scripts.recommendation_tracker import track_all_pending
    track_all_pending()
    
    # 2. 统计
    stats = compute_stats()
    
    print(f"\n各信号源本周表现:")
    print(f"{'信号源':25s} {'样本':>6} {'胜率':>8} {'均T+1':>8} {'状态':>10}")
    print("-" * 57)
    
    to_prune = []
    for source, s in sorted(stats.items()):
        active = s.get('active', True)
        status = "ACTIVE" if active else "已停用"
        win_ok = "🟢" if s['win_rate'] >= 50 else "🔴" if s['total'] >= 5 else "🟡"
        print(f"{win_ok} {source:22s} {s['total']:>6} {s['win_rate']:>7.1f}% {s['avg_t1_return']:>+7.2f}% {status:>10}")
        
        if s['total'] >= 5 and s['win_rate'] < 50:
            to_prune.append(source)
    
    # 3. 自动砍掉低胜率信号源
    if to_prune:
        print(f"\n自动砍掉以下低胜率信号源:")
        data = init_tracker()
        for source in to_prune:
            print(f"  ❌ {source} (胜率{stats[source]['win_rate']:.0f}%, 样本{stats[source]['total']}次)")
            data['source_stats'][source]['active'] = False
            data['source_stats'][source]['pruned_date'] = date.today().isoformat()
        save_tracker(data)
    else:
        print(f"\n✅ 所有活跃信号源表现达标")
    
    # 4. 输出本周最佳/最差推荐
    data = init_tracker()
    recs = data.get('recommendations', [])
    completed = [r for r in recs if r.get('result')]
    
    if completed:
        wins = sorted([r for r in completed if r['result'] == 'win'], 
                      key=lambda x: x.get('tracking', {}).get('1', {}).get('return', 0), reverse=True)
        losses = sorted([r for r in completed if r['result'] == 'loss'],
                        key=lambda x: x.get('tracking', {}).get('1', {}).get('return', 0))
        
        print(f"\n本周最佳推荐 (T+1收益):")
        for r in wins[:3]:
            t1 = r.get('tracking', {}).get('1', {}).get('return', 0)
            print(f"  🟢 {r['name']}({r['code']}) +{t1:.1f}% [{r['source']}]")
        
        print(f"\n本周最差推荐 (T+1收益):")
        for r in losses[:3]:
            t1 = r.get('tracking', {}).get('1', {}).get('return', 0)
            print(f"  🔴 {r['name']}({r['code']}) {t1:.1f}% [{r['source']}]")
    
    print(f"\n{'='*55}")

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()