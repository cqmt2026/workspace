#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cron_error_analysis.py - 分析Gateway Cron任务错误类型，按类别汇总"""
import subprocess, json, os, sys
from collections import defaultdict

BASE = r"C:\Users\Administrator\.openclaw"
CLI = r"C:\Users\Administrator\AppData\Roaming\npm\openclaw.cmd"
OUTPUT = os.path.join(BASE, "workspace", "memory", "日志", "cron_error_analysis.json")

def get_cron_jobs():
    try:
        r = subprocess.run(f'"{CLI}" gateway call cron.list', shell=True,
                           capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30)
        if r.returncode != 0:
            return None
        raw = r.stdout
        idx = raw.find('{')
        if idx < 0: return None
        data = json.loads(raw[idx:])
        return data.get('jobs', [])
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return None

def classify(name, error):
    if not error: return 'ok'
    e = error.lower()
    if 'rate limit' in e or 'token plan' in e or '每日额度已用完' in e or '限速模式' in e:
        return 'api_rate_limit'
    if 'channel' in e and ('weixin' in e or 'unsupported' in e):
        return 'channel_config'
    if 'exit code 2' in e or 'command exited' in e:
        return 'script_error'
    if 'timeout' in e:
        return 'timeout'
    if 'model' in e or 'unsupported model' in e:
        return 'model_unavailable'
    if 'network' in e or 'connection' in e:
        return 'network'
    return 'other'

def main():
    jobs = get_cron_jobs()
    if not jobs:
        print("无法获取Cron数据", file=sys.stderr)
        sys.exit(1)

    total = len(jobs)
    enabled = sum(1 for j in jobs if j.get('enabled', True))
    statuses = defaultdict(int)
    by_class = defaultdict(list)

    for j in jobs:
        status = j.get('lastRunStatus', 'unknown')
        error = j.get('lastRunError') or ''
        statuses[status] += 1
        cls = classify(j['name'], error)
        by_class[cls].append({
            'name': j['name'],
            'agent': j.get('agentId', ''),
            'error': error[:120] if error else '',
        })

    result = {'total': total, 'enabled': enabled, 'statuses': dict(statuses), 'by_class': {k: v for k, v in by_class.items()}}
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"总计: {total} | 启用: {enabled} | 禁用: {total-enabled}")
    print("\n运行状态分布:")
    for s, c in sorted(statuses.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")
    print("\n错误分类 (按规模排序):")
    for cls, items in sorted(by_class.items(), key=lambda x: -len(x[1])):
        print(f"\n  [{cls}] {len(items)}条:")
        for it in items[:5]:
            err_safe = it['error'].encode('gbk', errors='replace').decode('gbk')[:80]
            print(f"    - {it['name']} ({it['agent']}): {err_safe}")
        if len(items) > 5:
            print(f"    ... 还有 {len(items)-5} 条")
    print(f"\n报告已保存: {OUTPUT}")

if __name__ == '__main__':
    main()
