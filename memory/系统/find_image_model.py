# -*- coding: utf-8 -*-
import os, json

found = []
for root, dirs, files in os.walk(r'C:\Users\Administrator\.openclaw'):
    for f in files:
        if not f.endswith('.json'):
            continue
        full = os.path.join(root, f)
        try:
            with open(full, 'r', encoding='utf-8') as fp:
                content = fp.read()
                if 'imageModel' in content:
                    found.append((full, content))
        except:
            pass

if found:
    for path, content in found:
        print('File:', path)
        print(content[:1000])
        print('---')
else:
    print('No imageModel config found in .openclaw JSON files')

# Also check if there's a gateway config
gw_paths = [
    r'C:\Users\Administrator\.openclaw\gateway.json',
    r'C:\Users\Administrator\.openclaw\config\gateway.json',
    r'C:\Users\Administrator\AppData\Roaming\openclaw\gateway.json',
]
for p in gw_paths:
    if os.path.exists(p):
        print('Found gateway config:', p)
        with open(p, 'r', encoding='utf-8') as f:
            print(f.read()[:500])
