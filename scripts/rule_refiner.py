"""
rule_refiner.py — 每周从 corrections.md 提炼高频踩坑为系统规则

使用方式：
  python scripts/rule_refiner.py

提炼原则：
- 同一问题出现≥2次 → 升格为规则，写入子系统 MEMORY.md
- 出现1次但后果严重（数据丢失/不可恢复）→ 写入预防规则
- 出现1次且不影响后续 → 只记corrections.md，不升级

输出：
- 提炼报告：memory/日志/task/audit/rule_refine_YYYYMMDD.md
"""

import os
import re
import json
import sys
from collections import defaultdict
import io

WS = r'C:\Users\Administrator\.openclaw\workspace'
SYSTEMS = {
    '主系统': '',
    '投资': 'workspace-investment',
    '小说': 'workspace-novel',
    '自媒体': 'workspace-social',
    '数学动画': 'workspace-math',
    '微信小程序': 'workspace-weixin',
}

def find_corrections_files(ws):
    """找到所有corrections.md文件"""
    files = []
    for root, dirs, fs in os.walk(ws):
        for f in fs:
            if f == 'corrections.md':
                fp = os.path.join(root, f)
                # Skip memory subdirs that are just mirrors
                rel = os.path.relpath(fp, ws)
                files.append((rel, fp))
    return files

def extract_entries(content):
    """从corrections.md中提取每个踩坑条目"""
    entries = []
    lines = content.split('\n')
    
    current_entry = None
    in_entry = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect entry start: "## 2026-06-XX" or "## YYYY-MM-DD" or "### 数字."
        if re.match(r'^#{1,3}\s+\d{4}[-/]\d{2}[-/]\d{2}', stripped) or \
           (re.match(r'^#{1,3}\s+\d+\.', stripped) and len(stripped) < 100):
            if current_entry:
                entries.append(current_entry)
            current_entry = {'title': stripped, 'lines': [], 'start_line': i}
            in_entry = True
        elif re.match(r'^#{1,3}\s+\[\d{4}.*\]', stripped):
            if current_entry:
                entries.append(current_entry)
            current_entry = {'title': stripped, 'lines': [], 'start_line': i}
            in_entry = True
        elif in_entry and stripped.startswith('---') and len(stripped) == 3:
            if current_entry:
                entries.append(current_entry)
            current_entry = None
            in_entry = False
        elif in_entry and current_entry:
            current_entry['lines'].append(stripped)
    
    if current_entry:
        entries.append(current_entry)
    
    return entries

def classify_entries(entries):
    """将条目分为高频（≥2次）和低频（1次）"""
    # Group by root cause key
    by_root_cause = defaultdict(list)
    
    for entry in entries:
        # Extract root cause from entry
        title = entry.get('title', '')
        lines = entry.get('lines', [])
        
        # Try to find root cause description
        root_cause = title
        for line in lines:
            if '根因' in line:
                root_cause = line.replace('**根因**', '').replace('**根因**:', '').strip()
                break
        
        key = root_cause[:60]  # Truncate for grouping
        by_root_cause[key].append(entry)
    
    high_freq = {k: v for k, v in by_root_cause.items() if len(v) >= 2}
    single_severe = {k: v for k, v in by_root_cause.items() if len(v) == 1}
    
    return high_freq, single_severe

def find_severe_entries(entries):
    """识别严重后果的条目（数据丢失、不可恢复等）"""
    severe_keywords = ['数据丢失', '覆盖', '全损', '丢失', '不可恢复', '污染']
    severe = []
    for entry in entries:
        text = ' '.join(entry.get('lines', []))
        if any(kw in text for kw in severe_keywords):
            severe.append(entry)
    return severe

def main():
    print('=== 规则提炼器 ===')
    print(f'工作区: {WS}')
    
    all_entries = []
    corrections_files = find_corrections_files(WS)
    
    print(f'\n找到 {len(corrections_files)} 个 corrections.md 文件')
    
    for rel_path, fp in corrections_files:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        entries = extract_entries(content)
        print(f'  {rel_path:60s} → {len(entries)} 条踩坑')
        all_entries.extend([(rel_path, e) for e in entries])
    
    print(f'\n总踩坑条目: {len(all_entries)}')
    
    # Group by system
    by_system = defaultdict(list)
    for rel_path, entry in all_entries:
        # Determine which system
        sys_name = '其他'
        for name, prefix in SYSTEMS.items():
            if rel_path.startswith(prefix) if prefix else rel_path == rel_path:
                # Better matching
                if prefix:
                    if rel_path.startswith(prefix):
                        sys_name = name
                        break
                else:
                    if not rel_path.startswith('workspace-'):
                        sys_name = name
                        break
        
        by_system[sys_name].append((rel_path, entry))
    
    # Analyze each system
    print('\n=== 各系统分析 ===')
    report_lines = ['# 规则提炼报告', '', f'**生成时间**: {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}', '']
    
    for sys_name in ['主系统', '投资', '小说', '自媒体', '数学动画', '微信小程序']:
        entries = by_system.get(sys_name, [])
        if not entries:
            continue
        
        print(f'\n【{sys_name}】{len(entries)} 条')
        report_lines.append(f'## {sys_name}')
        report_lines.append(f'踩坑总数: {len(entries)}')
        
        # Group by root cause
        cause_groups = defaultdict(list)
        for rel_path, entry in entries:
            cause = entry.get('title', '')[:80]
            cause_groups[cause].append(entry)
        
        # Find duplicates
        duplicates = {k: v for k, v in cause_groups.items() if len(v) >= 2}
        
        if duplicates:
            print(f'  高频问题（≥2次）: {len(duplicates)} 类')
            report_lines.append(f'\n### ⚠️ 高频问题（≥2次，建议升格为规则）')
            for cause, group in sorted(duplicates.items(), key=lambda x: -len(x[1])):
                count = len(group)
                print(f'    [{count}次] {cause[:60]}')
                report_lines.append(f'- [{count}次] {cause}')
        else:
            report_lines.append('\n无高频重复问题')
        
        # Find severe entries
        severe = find_severe_entries([e[1] for e in entries])
        if severe:
            print(f'  严重后果: {len(severe)} 条')
            report_lines.append(f'\n### 🔴 严重后果（建议升格为预防规则）')
            for entry in severe:
                title = entry.get('title', '')[:80]
                report_lines.append(f'- {title}')
        
        # Already refined entries
        for rel_path, entry in entries:
            lines = ' '.join(entry.get('lines', []))
            if '已固化' in lines or '已修复' in lines:
                pass  # Already handled
        
        report_lines.append('')
    
    # Write report
    report_path = os.path.join(WS, 'memory', '日志', 'task', 'audit', 
                               f'rule_refine_{__import__("datetime").datetime.now().strftime("%Y%m%d")}.md')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f'\n报告已写入: {os.path.relpath(report_path, WS)}')

if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
