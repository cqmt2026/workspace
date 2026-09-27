# -*- coding: utf-8 -*-
"""
自动错误记录到陷阱手册
执行后自动检测新错误并追加到手册
"""

import os
import re
import json
from datetime import datetime

TRAP_MANUAL = r"C:\Users\Administrator\.openclaw\workspace\shared-knowledge\系统知识图谱与常见陷阱手册.md"
ERROR_LOG = r"C:\Users\Administrator\.openclaw\workspace\memory\当前错误记录.json"

def load_existing_traps():
    """加载已有陷阱"""
    traps = []
    if os.path.exists(TRAP_MANUAL):
        with open(TRAP_MANUAL, 'r', encoding='utf-8') as f:
            content = f.read()
        # 解析表格行
        for line in content.split('\n'):
            if line.startswith('| T'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 6:
                    traps.append({
                        'id': parts[1],
                        'system': parts[2],
                        'desc': parts[3],
                        'fix': parts[4],
                        'severity': parts[5],
                        'date': parts[6] if len(parts) > 6 else ''
                    })
    return traps

def save_trap(trap):
    """保存新陷阱"""
    traps = load_existing_traps()
    
    # 检查是否重复
    for t in traps:
        if t['desc'] == trap['desc'] and t['system'] == trap['system']:
            print(f"[SKIP] 陷阱已存在: {trap['id']}")
            return False
    
    # 生成新ID
    new_id = f"T{len(traps)+1:03d}"
    trap['id'] = new_id
    trap['date'] = datetime.now().strftime('%Y-%m-%d')
    
    # 追加到文件
    with open(TRAP_MANUAL, 'a', encoding='utf-8') as f:
        f.write(f"\n### {new_id}: {trap['desc']}\n\n")
        f.write(f"**现象：** {trap['phenomenon']}\n\n")
        f.write(f"**根因：** {trap['root_cause']}\n\n")
        f.write(f"**修复：** {trap['fix']}\n\n")
    
    print(f"[OK] 新陷阱已添加: {new_id}")
    return True

def detect_new_errors():
    """检测新错误（从错误日志）"""
    if not os.path.exists(ERROR_LOG):
        return []
    
    with open(ERROR_LOG, 'r', encoding='utf-8') as f:
        errors = json.load(f)
    
    # 过滤已记录的错误
    traps = load_existing_traps()
    recorded = [t['desc'] + t['system'] for t in traps]
    
    new_errors = []
    for err in errors:
        key = err.get('description', '') + err.get('system', '')
        if key not in recorded:
            new_errors.append(err)
    
    return new_errors

def main():
    print("=== 自动错误记录检查 ===")
    
    new_errors = detect_new_errors()
    
    if new_errors:
        print(f"发现 {len(new_errors)} 个新错误:")
        for err in new_errors:
            print(f"  - [{err.get('system', '未知')}] {err.get('description', '无描述')}")
        
        print("\n是否自动记录到陷阱手册？(y/N)")
        # 实际使用时应阻塞等待输入
    else:
        print("未发现新错误")

if __name__ == "__main__":
    main()
