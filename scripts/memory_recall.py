# -*- coding: utf-8 -*-
"""
Memory Recall - 记忆召回+注入式上下文
每天9:00/18:00运行，召回记忆写入context_cache.json，供各子系统引用
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'memory'))
from memory_ref import recall

CACHE_DIR = r'C:\Users\Administrator\.openclaw\workspace\memory'
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, 'context_cache.json')

QUERIES = {
    '小说': [('角色', '陆鸣 鉴城师'), ('情节', '情节 角色')],
    '投资': [('涨停', '涨停 板块 热点'), ('策略', '策略 信号')],
    '自媒体': [('爆款', '爆款 热点 抖音'), ('话题', '话题')],
    '系统': [('决策', '升级 决策'), ('日志', '工作日志')],
}

result = {'domains': {}, 'generated_at': os.environ.get('NOW', '')}
print('=== Memory Recall ===')
for domain, queries in QUERIES.items():
    r = recall(queries, top_k=3, max_total=5)
    entries = []
    for m in r['results']:
        entries.append({
            'label': m['_label'],
            'score': round(m['score'], 4),
            'text': m['text'],
            'category': m.get('category', ''),
        })
    result['domains'][domain] = entries
    print('[%s] %d条' % (domain, len(entries)))
    for e in entries[:3]:
        print('  [%.4f] %s' % (e['score'], e['text'][:60]))

with open(CACHE_FILE, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print()
print('上下文缓存已写入: %s' % CACHE_FILE)