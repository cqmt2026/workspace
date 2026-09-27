# -*- coding: utf-8 -*-
import os

# Search for openclaw config files
search_roots = [
    r'C:\Users\Administrator',
    r'C:\',
]

for base in search_roots:
    count = 0
    for root, dirs, files in os.walk(base):
        for f in files:
            if '.openclaw' in f.lower() or ('openclaw' in f.lower() and f.endswith(('.json','.yaml','.yml','.toml'))):
                print(os.path.join(root, f))
        count += 1
        if count > 5000:
            break
