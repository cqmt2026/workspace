import json
with open(r'C:\Users\Administrator\.openclaw\workspace\workspace-pv\data\output\llm_generated\llm_generated_20260820.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'Total: {len(data)} contents')
for i, c in enumerate(data):
    hook_len = len(c.get('hook',''))
    body_len = len(c.get('body',''))
    direction = c.get('direction','?')
    title = c.get('title','')[:40]
    print(f'[{i+1}] {direction:8s} | hook={hook_len:3d} | body={body_len:4d} | {title}...')
