#!/usr/bin/env python3
"""
系统Cron任务健康分析
从临时JSON读取所有任务，分析成功率/失败模式
"""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open(r"C:\Users\Administrator\.openclaw\workspace\tmp_cron_list.json", encoding='utf-8-sig') as f:
    data = json.load(f)

jobs = data.get('jobs', [])
print(f"总任务数: {len(jobs)}")

# 状态统计
stats = {}
for j in jobs:
    status = j.get('status', 'unknown')
    stats[status] = stats.get(status, 0) + 1

print("\n状态分布:")
for k, v in sorted(stats.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

# 提取连续失败次数 (从status字段如 error (4x) 或单独字段)
print("\n连续失败任务 (error x次):")
failures = []
for j in jobs:
    status = j.get('status', '')
    enabled = j.get('enabled', True)
    name = j.get('name', '')
    if 'error' in status and enabled:
        m = re.search(r'\((\d+)x\)', status)
        count = int(m.group(1)) if m else 1
        failures.append((count, name, j.get('id',''), j.get('model','')))
        if count >= 3:
            print(f"  [{count}x] {name} | model={j.get('model','')}")
