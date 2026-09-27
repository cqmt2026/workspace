#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-P2检查清单工具
执行前必须运行此脚本，确认所有检查项
"""
import sys
import os

def print_checklist():
    print("=" * 60)
    print("【执行前检查清单】")
    print("=" * 60)
    print()
    
    # P0 - 阻塞级
    print("[P0] 阻塞级（必须执行）")
    print("-" * 40)
    print("[ ] 1. 已复述主人需求并确认")
    print("[ ] 2. 已备份可能影响的文件")
    print("[ ] 3. 日期计算已用工具验证")
    print("[ ] 4. 路径验证：写入位置正确")
    print()
    
    # P1 - 效率级
    print("[P1] 效率级（应当执行）")
    print("-" * 40)
    print("[ ] 5. 已检查是否有现成工具可复用")
    print("[ ] 6. 报告输出前已复核一致性")
    print("[ ] 7. 复杂操作已用grep确认复用性")
    print()
    
    # P2 - 优化级
    print("[P2] 优化级（尝试执行）")
    print("-" * 40)
    print("[ ] 8. 已评估并行执行可能性")
    print("[ ] 9. 已设置细粒度检查点")
    print()
    
    # 方法论检查
    print("[方法论] 检查")
    print("-" * 40)
    print("[ ] 10. 第一性原理拆解已完成（复杂任务）")
    print("[ ] 11. Ponytail检查已完成（YAGNI）")
    print("[ ] 12. 30分钟断点已评估")
    print()
    
    print("=" * 60)
    print("确认以上检查项后，方可执行任务")
    print("=" * 60)

def validate_execution():
    """验证执行是否规范"""
    checks = [
        ("需求复述", False),
        ("文件备份", False),
        ("日期验证", False),
        ("路径验证", False),
        ("工具复用", False),
        ("一致性复核", False),
        ("并行评估", False),
        ("方法论检查", False),
    ]
    
    return checks

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--validate':
        checks = validate_execution()
        print("\n【执行验证结果】")
        for name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {name}")
    else:
        print_checklist()
