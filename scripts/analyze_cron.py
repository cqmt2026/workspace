# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = json.load(open(r'C:\Users\Administrator\.openclaw\workspace\memory\cron_list.json', encoding='utf-8'))
jobs = d.get('jobs', [])
print(f"总任务数: {len(jobs)}")
print("="*50)

# 找错误
print("【连续错误 >= 2】")
for j in jobs:
    state = j.get('state', {})
    errs = state.get('consecutiveErrors', 0)
    if errs >= 2:
        print(f"  ❌ {j['name']}: 连续错误={errs}, 最后状态={state.get('lastStatus','')}, 错误={state.get('lastError','N/A')}")

# 找大量跳过
print("\n【连续跳过 > 20】")
for j in jobs:
    state = j.get('state', {})
    skips = state.get('consecutiveSkipped', 0)
    if skips > 20:
        print(f"  ⚠️ {j['name']}: 连续跳过={skips}, 错误={state.get('lastError','N/A')}")

# 找error状态
print("\n【lastStatus=error】")
for j in jobs:
    state = j.get('state', {})
    if state.get('lastStatus') == 'error':
        print(f"  ❌ {j['name']}: lastError={state.get('lastError','N/A')}, consecutiveErrors={state.get('consecutiveErrors',0)}")

# 检查脚本漏检原因
print("\n[调试] self_heal_l1.py 逻辑分析:")
print("  - check_errors() 只检查 consecutiveErrors >= 2")
print("  - 已知问题会被跳过（Hot-Topic-Finder等）")
print("  - 当前发现的任务不在 KNOWN_ISSUES 中")
print("  - 问题：脚本返回 PASS，但实际有4个错误任务")
print("\n[结论] 脚本的 get_cron_jobs() 可能未正确解析输出")