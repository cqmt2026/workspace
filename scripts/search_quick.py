import os, datetime

# Quick search in recent files only
keywords = ['职业避坑', '20个职业', 'career', '职场避坑']
search_dirs = [
    r'C:\Users\Administrator\.openclaw\workspace\memory',
    r'C:\Users\Administrator\.openclaw\workspace\workspace-social',
    r'C:\Users\Administrator\.openclaw\workspace\workspace-novel',
    r'C:\Users\Administrator\.openclaw\workspace\shared-knowledge',
]

for base in search_dirs:
    if not os.path.exists(base):
        continue
    for root, dirs, files in os.walk(base):
        for f in files:
            if not (f.endswith('.md') or f.endswith('.json')):
                continue
            path = os.path.join(root, f)
            mtime = os.path.getmtime(path)
            # Only search files from last 7 days
            if mtime < datetime.datetime.now().timestamp() - 7*86400:
                continue
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                for kw in keywords:
                    if kw in content:
                        rel = os.path.relpath(path, r'C:\Users\Administrator\.openclaw\workspace')
                        print(f'{rel} [{kw}]')
                        break
            except:
                pass

print('Done')
