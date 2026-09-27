# -*- coding: utf-8 -*-
"""
错误模式检测脚本
自动扫描修复日志，检测重复错误模式
"""

import os
import re
import json
from datetime import datetime, timedelta
from collections import Counter

LOG_DIR = r"C:\Users\Administrator\.openclaw\workspace\memory\日志\修复日志"
OUTPUT_FILE = r"C:\Users\Administrator\.openclaw\workspace\memory\错误模式分析.json"

def parse_fix_log(filepath):
    """解析修复日志"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取关键信息
        patterns = {
            'date': r'fix_(\d{8})_',
            'system': r'fix_\d{8}_(\w+)_',
            'issue': r'##.*?(?=##|$)',
            'root_cause': r'根因.*?(?:\n\s*).*(?=\n\n|\Z)',
        }
        
        result = {
            'file': os.path.basename(filepath),
            'date': None,
            'system': None,
            'issues': [],
            'root_causes': []
        }
        
        # 提取日期
        date_match = re.search(patterns['date'], filepath)
        if date_match:
            result['date'] = date_match.group(1)
        
        # 提取子系统
        system_match = re.search(patterns['system'], filepath)
        if system_match:
            result['system'] = system_match.group(1)
        
        # 提取问题和根因
        lines = content.split('\n')
        for line in lines:
            if '根因' in line or '原因' in line:
                result['root_causes'].append(line.strip())
            if '问题' in line or 'bug' in line.lower():
                result['issues'].append(line.strip())
        
        return result
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None

def detect_patterns(logs):
    """检测错误模式"""
    systems = [l['system'] for l in logs if l['system']]
    system_counts = Counter(systems)
    
    # 检测重复根因
    root_causes = []
    for log in logs:
        root_causes.extend(log['root_causes'])
    
    # 简化根因关键词
    keywords = []
    for rc in root_causes:
        keywords.extend(re.findall(r'[一-龥]{2,4}', rc))
    
    keyword_counts = Counter(keywords)
    repeated = {k: v for k, v in keyword_counts.items() if v > 1}
    
    return {
        'system_distribution': dict(system_counts),
        'repeated_keywords': repeated,
        'total_logs': len(logs)
    }

def main():
    print("=== 错误模式检测 ===")
    
    if not os.path.exists(LOG_DIR):
        print(f"日志目录不存在: {LOG_DIR}")
        return
    
    # 解析所有日志
    logs = []
    for file in os.listdir(LOG_DIR):
        if file.endswith('.md') and file.startswith('fix_'):
            filepath = os.path.join(LOG_DIR, file)
            log = parse_fix_log(filepath)
            if log:
                logs.append(log)
    
    print(f"解析日志数: {len(logs)}")
    
    # 检测模式
    analysis = detect_patterns(logs)
    
    # 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    print(f"\n分析结果:")
    print(f"  总日志数: {analysis['total_logs']}")
    print(f"  子系统分布: {analysis['system_distribution']}")
    print(f"  重复关键词: {analysis['repeated_keywords']}")
    print(f"\n结果已保存至: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
