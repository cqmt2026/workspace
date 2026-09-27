#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第一性原理拆解工具
复杂任务执行前必须进行四步拆解
"""
import sys

def first_principles_analysis(task):
    """第一性原理四步拆解"""
    
    print("=" * 70)
    print("[第一性原理拆解]")
    print("=" * 70)
    print()
    print(f"任务: {task}")
    print()
    
    # 第一步：砸碎表象
    print("[1] 第一步：砸碎表象")
    print("-" * 50)
    print("真正的需求是什么？连问5个为什么：")
    print("  Q1: 为什么要做这个任务？")
    print("  A1: [待填写]")
    print("  Q2: 为什么有这个需求？")
    print("  A2: [待填写]")
    print("  Q3: 为什么会有这个问题？")
    print("  A3: [待填写]")
    print("  Q4: 为什么会有这个原因？")
    print("  A4: [待填写]")
    print("  Q5: 为什么会有这个根源？")
    print("  A5: [待填写]")
    print()
    print("  根因: [待填写]")
    print()
    
    # 第二步：倒空烂苹果
    print("[2] 第二步：倒空烂苹果")
    print("-" * 50)
    print("区分物理定律和人为规定：")
    print("  [ ] 物理定律（不可跨越）：")
    print("      - [待填写]")
    print("  [ ] 人为规定（可以打破）：")
    print("      - [待填写]")
    print()
    
    # 第三步：重拼乐高
    print("[3] 第三步：重拼乐高")
    print("-" * 50)
    print("从原点重新推导最优解：")
    print("  最优解应该是: [待填写]")
    print("  理由是: [待填写]")
    print()
    
    # 第四步：找裂缝
    print("[4] 第四步：找裂缝")
    print("-" * 50)
    print("对比理论最优和行业现实：")
    print("  理论最优: [待填写]")
    print("  行业现实: [待填写]")
    print("  落差处（发力点）: [待填写]")
    print()
    
    print("=" * 70)
    print("拆解完成后，方可执行任务")
    print("=" * 70)

def ponytail_check(task):
    """Ponytail最少可行检查"""
    print()
    print("[Ponytail检查]")
    print("-" * 50)
    print(f"任务: {task}")
    print()
    print("[ ] YAGNI: 这个功能真的需要吗？")
    print("  答案: [是/否]")
    print()
    print("[ ] 有现成工具吗？")
    print("  答案: [有/无，如有请列出]")
    print()
    print("[ ] 最小方案是什么？")
    print("  答案: [待填写]")
    print()
    print("[ ] 能砍掉什么？")
    print("  答案: [待填写]")
    print()
    print("=" * 70)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python first_principles.py <任务描述>")
        print()
        print("示例:")
        print('  python first_principles.py "生成下周三天拨打清单"')
        print('  python first_principles.py "开发CRM数据验证工具"')
        sys.exit(1)
    
    task = sys.argv[1]
    first_principles_analysis(task)
    ponytail_check(task)
