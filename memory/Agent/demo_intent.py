# -*- coding: utf-8 -*-
"""意图识别演示"""

import sys
from pathlib import Path

# 添加 memory/Agent 路径
sys.path.insert(0, str(Path(r'C:\Users\Administrator\.openclaw\workspace\memory\Agent')))

from agent_dispatcher import AgentDispatcher

dispatcher = AgentDispatcher()

# 测试用户消息
test_messages = [
    '创作第 52 章',
    '优化一下第 50 章',
    '审核第 51 章',
    '写一篇小红书笔记',
    '分析一下贵州茅台',
]

print('='*60)
print('意图识别演示')
print('='*60)

for msg in test_messages:
    intent = dispatcher.dispatch(msg)
    print(f'"{msg}" -> {intent}')
