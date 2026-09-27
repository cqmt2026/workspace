#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令复述确认工具
接收主人指令后，必须先复述确认
"""
import sys

def confirm_instruction(user_input):
    """复述主人指令并等待确认"""
    print("=" * 60)
    print("【指令复述确认】")
    print("=" * 60)
    print()
    print("主人指令：")
    print(f"  {user_input}")
    print()
    print("我的理解：")
    print("  1. 核心需求：[待填写]")
    print("  2. 约束条件：[待填写]")
    print("  3. 交付标准：[待填写]")
    print("  4. 预计耗时：[待填写]")
    print()
    print("-" * 40)
    print("请确认以上理解是否正确？")
    print("输入 'y' 继续，输入 'n' 修正")
    print("=" * 60)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        confirm_instruction(sys.argv[1])
    else:
        print("用法: python confirm.py \"主人指令\"")
        print()
        print("示例:")
        print('  python confirm.py "生成下周三天拨打清单"')
