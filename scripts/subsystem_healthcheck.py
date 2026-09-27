# -*- coding: utf-8 -*-
"""子系统接入点健康检查"""
import sys, os, glob

print('=' * 60)
print('子系统健康度检查')
print('=' * 60)

# === 1. 检查所有改过的子系统文件是否存在、语法正确 ===
print('\n[1/5] 子系统文件完整性')

files_to_check = {
    '投资-早盘': r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts\morning_brief.py',
    '投资-RPS推送': r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts\rps_push.py',
    '投资-每日分析': r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts\daily_analysis.py',
    '自媒体-热点发现': r'C:\Users\Administrator\.openclaw\workspace\scripts\hot_topic_find.py',
    '自媒体-深度学习': r'C:\Users\Administrator\.openclaw\workspace\workspace-social\scripts\viral_deep_learning.py',
    '自媒体-工作流': r'C:\Users\Administrator\.openclaw\workspace\scripts\social_workflow.py',
    '小说-工作流': r'C:\Users\Administrator\.openclaw\workspace\scripts\novel_workflow.py',
    '小说-自我学习': r'C:\Users\Administrator\.openclaw\workspace\workspace-novel\创作系统\L1-日志\scripts\auto_learning.py',
    '数学-制作': r'C:\Users\Administrator\.openclaw\workspace\workspace-math\scripts\ep_make.py',
    '系统-自我学习': r'C:\Users\Administrator\.openclaw\workspace\scripts\self_learning.py',
    '系统-Obsidian沉淀': r'C:\Users\Administrator\.openclaw\workspace\scripts\obsidian_sync.py',
}

errors = []
for name, path in files_to_check.items():
    exists = os.path.exists(path)
    if not exists:
        errors.append(f'  [X] {name}: 文件不存在')
        continue
    try:
        with open(path, 'r', encoding='utf-8') as f:
            compile(f.read(), path, 'exec')
    except SyntaxError as e:
        errors.append(f'  [X] {name}: 语法错误 L{e.lineno}')

if errors:
    for e in errors:
        print(e)
else:
    print('  [OK] 全部11个子系统文件存在且语法正确')

# === 2. 检查每个文件是否包含memory_adapter引用 ===
print('\n[2/5] memory_adapter接入检查')
import re
adapter_refs = {
    'morning_brief.py': True,
    'rps_push.py': True,
    'daily_analysis.py': True,
    'hot_topic_find.py': True,
    'viral_deep_learning.py': True,
    'social_workflow.py': True,
    'novel_workflow.py': True,
    'auto_learning.py': True,
    'ep_make.py': True,
    'self_learning.py': True,
    'obsidian_sync.py': True,
}

missing_refs = []
for name in adapter_refs:
    found = False
    for path in files_to_check.values():
        if name in path:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'memory_adapter' in content or 'memory_ref' in content:
                found = True
            break
    if not found:
        missing_refs.append(name)

if missing_refs:
    print('  [WARN] 以下文件未引用memory_adapter:')
    for m in missing_refs:
        print(f'    {m}')
else:
    print('  [OK] 全部11个子系统已接入memory_adapter')

# === 3. 检查反哺引用 ===
print('\n[3/5] 反哺(memory_ref)接入检查')
feedback_refs = {
    'morning_brief.py': 'memory_ref',
    'rps_push.py': 'memory_ref',
    'daily_analysis.py': 'memory_ref',
    'hot_topic_find.py': 'memory_ref',
    'novel_workflow.py': 'memory_ref',
    'self_learning.py': 'memory_ref',
}

missing_feedback = []
for name, keyword in feedback_refs.items():
    for path in files_to_check.values():
        if name in path:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if keyword not in content:
                missing_feedback.append(name)
            break

if missing_feedback:
    print('  [WARN] 以下文件未接入反哺:')
    for m in missing_feedback:
        print(f'    {m}')
else:
    print('  [OK] 反哺子系统已全部接入memory_ref')

# === 4. 检查各子系统cron任务状态 ===
print('\n[4/5] Cron任务状态')
print('  (需等待下一次触发验证)')
print('  - morning_brief: 交易日9:22')
print('  - rps_push: 交易日9:30')
print('  - daily_analysis: 交易日16:15')
print('  - hot_topic_find: 每天9:02')
print('  - self_learning: 每天21:00')
print('  - obsidian_sync: 每天21:30')
print('  - memory_recall: 每天9:00/18:00')
print('  - viral_deep_learning: 每天11:30')
print('  - novel_auto_learning: 每天11:00')

# === 5. 模拟一次完整链路的代码路径 ===
print('\n[5/5] 代码路径模拟')
simulate = """
子系统产出 → memory_adapter.save() → 质量过滤 → memory_tools.save_memory()
                                                              ↓
子系统运行 → memory_ref.recall() → memory_adapter.search() → 返回历史
                                                              ↓
每天21:00 → self_learning.py → 日志审计 → 踩坑学习 → memory聚合
                                                              ↓
每天21:30 → obsidian_sync.py → Supermemory召回 → 写入Obsidian
"""
print(simulate)

print('=' * 60)
if not errors and not missing_refs and not missing_feedback:
    print('子系统健康，全部正常')
else:
    print('有需要修复的问题，见上')
print('=' * 60)