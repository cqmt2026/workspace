import os
import glob
import json

# Search for career-related files
paths = [
    r'C:\Users\Administrator\.openclaw\workspace\workspace-social',
    r'C:\Users\Administrator\.openclaw\workspace\shared-knowledge',
    r'C:\Users\Administrator\.openclaw\workspace\memory'
]

results = []
for p in paths:
    if os.path.exists(p):
        # Search for files with '职业' or 'career' in name
        for f in glob.glob(os.path.join(p, '**', '*职业*'), recursive=True):
            results.append(f'[{os.path.basename(p)}] {os.path.relpath(f, p)}')
        for f in glob.glob(os.path.join(p, '**', '*career*'), recursive=True):
            results.append(f'[{os.path.basename(p)}] {os.path.relpath(f, p)}')
        # Search in hot topics
        if '热点选题库' in p:
            for f in glob.glob(os.path.join(p, '**', '*.json'), recursive=True):
                try:
                    with open(f, 'r', encoding='utf-8') as fp:
                        data = json.load(fp)
                    if isinstance(data, list):
                        for item in data:
                            title = item.get('title', '')
                            if '职业' in title or '避坑' in title:
                                results.append(f'{f}: {title[:60]}')
                except:
                    pass

print(f'Found {len(results)} career-related items:')
for r in results[-15:]:
    print(f'  {r}')
