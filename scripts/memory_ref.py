# -*- coding: utf-8 -*-
"""
memory_ref.py v3.1 — 多DB分库版本
每个子系统只搜自己的domain，彻底解决污染
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'memory'))
from memory_adapter import search

def recall(queries, top_k=3, max_total=6, domain=None):
    """
    多维度召回历史记忆（限domain）
    queries: [('标签', '搜索词'), ...]
    """
    seen = set()
    results = []
    for label, q in queries:
        r = search(q, top_k=top_k, domain=domain)
        for m in r['results']:
            if m['text'] not in seen:
                seen.add(m['text'])
                m['_label'] = label
                results.append(m)
    results.sort(key=lambda x: x['score'], reverse=True)
    results = results[:max_total]

    summary_parts = []
    for m in results:
        summary_parts.append(f"[{m['score']:.2f}] {m['text'][:60]}")

    return {
        'count': len(results),
        'results': results,
        'summary': '\n'.join(summary_parts) if summary_parts else '（无相关历史记忆）'
    }

def format_for_prompt(recall_result):
    if recall_result['count'] == 0:
        return ''
    lines = ['\n[历史记忆参考]']
    for m in recall_result['results']:
        lines.append(f"  [{m['_label']}] ({m['score']:.2f}) {m['text'][:100]}")
    return '\n'.join(lines)

# ========== 子系统专用召回（各自搜自己的domain）==========

def recall_investment(context='今日开盘'):
    return recall([
        ('策略', '涨停 策略'),
        ('分析', '市场 板块'),
        ('日志', '工作日志'),
    ], domain='investment')

def recall_novel(context='当前章节'):
    return recall([
        ('角色', '陆鸣'),
        ('情节', '情节'),
    ], domain='novel')

def recall_social(context='今日热点'):
    return recall([
        ('爆款', '爆款 热点'),
        ('话题', '话题'),
    ], domain='social')

def recall_system(context='今日维护'):
    return recall([
        ('决策', '升级 决策'),
        ('日志', '工作日志'),
    ], domain='system')

def recall_math(context='今日制作'):
    return recall([
        ('制作', '动画 制作'),
    ], domain='math')

# ========== 跨域搜索（需要时手动调用）==========

def recall_cross(query, top_k=5):
    """跨所有domain搜索，返回时标注来源"""
    r = search(query, top_k=top_k, domain='*')
    return r


if __name__ == '__main__':
    print('=== 域内搜索（无污染） ===')
    r = recall_novel()
    print(f'小说域: {r["count"]}条')
    print(r['summary'])
    print()

    r = recall_investment()
    print(f'投资域: {r["count"]}条')
    print(r['summary'])
    print()

    print('=== 跨域搜索 ===')
    r = recall_cross('陆鸣', 5)
    print(f'跨域: {r["count"]}条')
    for m in r['results']:
        print(f'  [{m.get("_domain","?")}] [{m["score"]:.4f}] {m["text"][:40]}')