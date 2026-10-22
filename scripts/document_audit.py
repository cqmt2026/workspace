#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""历史文档整理与优化评估"""
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

ws = r'C:\Users\Administrator\.openclaw\workspace'

print("=" * 70)
print("历史文档整理与优化评估报告")
print("=" * 70)

# 1. 核心文档完整性检查
print("\n【1. 核心文档完整性检查】")
core_docs = {
    'SOUL.md': ('总经理定位', '2026-09-27'),
    'USER.md': ('主人偏好', '2026-09-25'),
    'AGENTS.md': ('工作规则/方法论', '2026-09-25'),
    'MEMORY.md': ('系统记忆', '2026-10-18'),
    'HEARTBEAT.md': ('Cron任务表', '2026-09-25'),
    'coding-standards.md': ('编码规范', '2026-09-25'),
    'TOOLS.md': ('工具笔记', '2026-10-17'),
}

for f, (desc, date) in core_docs.items():
    path = os.path.join(ws, f)
    if os.path.exists(path):
        size = os.path.getsize(path)
        status = '✅' if size > 1000 else '⚠️ 过小'
        print(f"  {status} {f}: {size//1024}KB ({desc})")
    else:
        print(f"  ❌ {f}: 缺失")

# 2. 文档版本一致性检查
print("\n【2. 文档版本一致性检查】")
agents_path = os.path.join(ws, 'AGENTS.md')
memory_path = os.path.join(ws, 'MEMORY.md')

def check_version_consistency():
    issues = []
    
    # 检查AGENTS.md版本
    if os.path.exists(agents_path):
        with open(agents_path, 'r', encoding='utf-8') as f:
            agents_content = f.read()
        if 'v1.5' not in agents_content and 'v1.6' not in agents_content:
            issues.append('⚠️ AGENTS.md缺少方法论版本标记')
    
    # 检查MEMORY.md版本
    if os.path.exists(memory_path):
        with open(memory_path, 'r', encoding='utf-8') as f:
            memory_content = f.read(500)
        if 'V3.' not in memory_content:
            issues.append('⚠️ MEMORY.md版本可能过旧')
    
    return issues

version_issues = check_version_consistency()
if version_issues:
    for issue in version_issues:
        print(f"  {issue}")
else:
    print("  ✅ 版本信息一致")

# 3. 知识库完整性检查
print("\n【3. 知识库完整性检查】")
knowledge_dirs = [
    ('shared-knowledge', '共享知识库'),
    ('memory', '记忆系统'),
    ('skills', '技能模块'),
]

for d, desc in knowledge_dirs:
    path = os.path.join(ws, d)
    if os.path.exists(path):
        count = len(os.listdir(path))
        print(f"  ✅ {d}/ ({desc}): {count}项")
    else:
        print(f"  ❌ {d}/: 缺失")

# 4. 历史日志检查
print("\n【4. 历史日志检查】")
memory_dir = os.path.join(ws, 'memory')
logs = []
if os.path.exists(memory_dir):
    for f in os.listdir(memory_dir):
        if f.endswith('.md') and f.startswith('2026'):
            logs.append(f)
print(f"  日志文件数: {len(logs)}个")

# 检查最近日志
recent_logs = sorted(logs)[-5:] if logs else []
print(f"  最近5个日志:")
for log in recent_logs:
    path = os.path.join(memory_dir, log)
    size = os.path.getsize(path) if os.path.exists(path) else 0
    print(f"    {log}: {size//1024}KB")

# 5. 优化建议
print("\n【5. 优化建议】")
recommendations = []

# 5.1 文档同步
print("\n  5.1 文档同步检查:")
# 检查HEARTBEAT.md与当前Cron是否一致
heartbeat_path = os.path.join(ws, 'HEARTBEAT.md')
if os.path.exists(heartbeat_path):
    with open(heartbeat_path, 'r', encoding='utf-8') as f:
        heartbeat_content = f.read()
    # 检查是否引用了已删除的子系统
    if 'workspace-pv' in heartbeat_content:
        recommendations.append('⚠️ HEARTBEAT.md引用了已废弃的workspace-pv')
    if 'workspace-novel' not in heartbeat_content:
        recommendations.append('⚠️ HEARTBEAT.md缺少workspace-novel相关任务')

# 5.2 陷阱手册更新
print("\n  5.2 陷阱手册检查:")
trap_manual = os.path.join(ws, 'shared-knowledge', '系统知识图谱与常见陷阱手册.md')
if os.path.exists(trap_manual):
    with open(trap_manual, 'r', encoding='utf-8') as f:
        trap_content = f.read()
    if 'T015' in trap_content or 'T016' in trap_content:
        print("    ✅ 陷阱手册已包含T015-T018新条目")
    else:
        recommendations.append('⚠️ 陷阱手册缺少T015-T018新条目')
else:
    recommendations.append('❌ 陷阱手册不存在')

# 5.3 脚本一致性
print("\n  5.3 脚本一致性检查:")
scripts_dir = os.path.join(ws, 'scripts')
if os.path.exists(scripts_dir):
    # 检查关键脚本是否存在
    critical_scripts = ['cn_io.py', 'humanize_text.py', 'obsidian_sync.py']
    for script in critical_scripts:
        if os.path.exists(os.path.join(scripts_dir, script)):
            print(f"    ✅ {script} 存在")
        else:
            recommendations.append(f'⚠️ {script} 缺失')

# 5.4 子系统文档
print("\n  5.4 子系统文档检查:")
subsystems = ['workspace-novel', 'workspace-social', 'workspace-investment', 
              'workspace-math', 'workspace-maphot', 'workspace-baiduagent', 'workspace-weixin']
for sub in subsystems:
    sub_path = os.path.join(ws, sub)
    if os.path.exists(sub_path):
        # 检查是否有核心文档
        core_files = ['SOUL.md', 'AGENTS.md', 'MEMORY.md']
        has_core = all(os.path.exists(os.path.join(sub_path, f)) for f in core_files)
        status = '✅' if has_core else '⚠️'
        print(f"    {status} {sub}: {'完整' if has_core else '缺少核心文档'}")
        if not has_core:
            recommendations.append(f'⚠️ {sub}缺少核心文档')

# 6. 总结
print("\n" + "=" * 70)
print("优化建议汇总:")
if recommendations:
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
else:
    print("  ✅ 未发现明显问题")
print("=" * 70)
