import os, glob, re, datetime

keywords = ['职业避坑', '20个职业', 'career', '职场避坑', '20 careers']
found = []
for root, dirs, files in os.walk(r'C:\Users\Administrator\.openclaw\workspace'):
    for f in files:
        if f.endswith('.md') or f.endswith('.json'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                for kw in keywords:
                    if kw in content:
                        mtime = os.path.getmtime(path)
                        found.append((mtime, os.path.relpath(path, r'C:\Users\Administrator\.openclaw\workspace'), kw))
                        break
            except:
                pass

found.sort(key=lambda x: x[0], reverse=True)
print(f'Found {len(found)} files:')
for mtime, path, kw in found[:20]:
    dt = datetime.datetime.fromtimestamp(mtime).strftime('%m-%d %H:%M')
    print(f'  {dt} {path} [{kw}]')
