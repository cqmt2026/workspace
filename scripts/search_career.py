import os
import glob
import json

# Search for career-related topics
keywords = ['职业', 'career', '20个', '避坑', '指南', 'top 20']

results = []
for root, dirs, files in os.walk(r'C:\Users\Administrator\.openclaw\workspace'):
    for f in files:
        if f.endswith('.md') or f.endswith('.json'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                for kw in keywords:
                    if kw in content and os.path.getmtime(path) > 1754073600:
                        results.append((os.path.relpath(path, r'C:\Users\Administrator\.openclaw\workspace'), kw))
                        break
            except:
                pass

print(f'Found {len(results)} files with career keywords (Aug 2-3):')
for r in results[:20]:
    print(f'  {r[0]}: {r[1]}')
