# -*- coding: utf-8 -*-
import os, json

for root, dirs, files in os.walk(r'C:\Users\Administrator\.openclaw'):
    for f in files:
        if f.endswith('.json'):
            full = os.path.join(root, f)
            try:
                with open(full, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    if 'imageModel' in content or 'image_model' in content or 'defaultImageModel' in content:
                        print(full)
                        print(content[:800])
                        print('---')
            except Exception as e:
                pass
