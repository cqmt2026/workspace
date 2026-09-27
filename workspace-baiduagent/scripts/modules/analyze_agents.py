import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

# 读取配置
f = open(r'C:\Users\Administrator\.openclaw\openclaw.json', 'r', encoding='utf-8')
c = json.load(f)
f.close()

print('=== Agent 配置清单 ===')
agents = c.get('agents', {}).get('entries', {})
for name, info in agents.items():
    label = info.get('name', '未命名')
    ws = info.get('workspace', '')
    model_info = info.get('model', {})
    if isinstance(model_info, dict):
        model = model_info.get('primary', 'default')
    else:
        model = 'default'
    ws_short = ws.split('\\')[-1] if ws else ''
    print(f'{name:12s} | {label:15s} | model={model} | ws={ws_short}')

print(f'\n总计: {len(agents)} 个Agent')

print('\n=== Cron Jobs ===')
cron_jobs = c.get('cron', {}).get('jobs', [])
print(f'数量: {len(cron_jobs)}')
for j in cron_jobs:
    print(f"  - {j.get('label','')} | agent={j.get('agentId','')}")

print('\n=== Bindings ===')
for b in c.get('bindings', []):
    print(f"  agent={b.get('agentId')} channel={b.get('match',{}).get('channel','')}")

# 查找各agent核心文档
print('\n=== 各Agent核心文档 ===')
agents_dir = r'C:\Users\Administrator\.openclaw\agents'
for agent_name in sorted(os.listdir(agents_dir)):
    if agent_name.startswith('.'): continue
    agent_path = os.path.join(agents_dir, agent_name)
    if not os.path.isdir(agent_path): continue
    files_found = []
    for fname in ['SOUL.md', 'IDENTITY.md', 'AGENTS.md', 'MEMORY.md']:
        fpath = os.path.join(agent_path, fname)
        if os.path.exists(fpath):
            size = os.path.getsize(fpath)
            files_found.append(f'{fname}({size//1024}KB)')
        # 也检查agent子目录
        fpath2 = os.path.join(agent_path, 'agent', fname)
        if os.path.exists(fpath2):
            size = os.path.getsize(fpath2)
            files_found.append(f'agent/{fname}({size//1024}KB)')
    if files_found:
        print(f'[{agent_name}] {", ".join(files_found)}')
