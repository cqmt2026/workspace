# -*- coding: utf-8 -*-
"""
子 Agent 调用完整演示
"""

import sys
from pathlib import Path

# 添加 memory/Agent 路径
sys.path.insert(0, str(Path(r'C:\Users\Administrator\.openclaw\workspace\memory\Agent')))

from agent_dispatcher import AgentDispatcher

print('='*60)
print('子 Agent 调用演示')
print('='*60)

# 1. 意图识别
dispatcher = AgentDispatcher()

test_messages = [
    '创作第 52 章',
    '优化一下第 50 章',
    '审核第 51 章',
    '写一篇小红书笔记',
    '分析一下贵州茅台',
    '陆鸣的新项目',
]

print('\n【步骤 1: 意图识别】')
print('-'*60)
for msg in test_messages:
    agent = dispatcher.dispatch(msg)
    print(f'"{msg}" → {agent or "main(主 Agent)"}')

# 2. 模拟派发任务
print('\n【步骤 2: 模拟派发任务】')
print('-'*60)

def simulate_spawn(agent_id: str, task: str):
    """模拟 sessions_spawn 调用"""
    workspace_map = {
        'novel': r'C:\Users\Administrator\.openclaw\workspace\workspace-novel',
        'social': r'C:\Users\Administrator\.openclaw\workspace\workspace-social',
        'investment': r'C:\Users\Administrator\.openclaw\workspace\workspace-investment',
    }
    
    ws = workspace_map.get(agent_id, r'C:\Users\Administrator\.openclaw\workspace')
    
    print(f'派发任务给 {agent_id} Agent:')
    print(f'  任务：{task}')
    print(f'  workspace: {ws}')
    print(f'  代码示例:')
    print(f'    sessions_spawn(')
    print(f'        task="{task}",')
    print(f'        agentId="{agent_id}",')
    print(f'        mode="run",')
    print(f'        cwd=r"{ws}",')
    print(f'    )')
    print()

# 演示派发
for msg in test_messages:
    agent = dispatcher.dispatch(msg)
    if agent:
        simulate_spawn(agent, msg)

print('='*60)
print('演示完成！')
print('='*60)
