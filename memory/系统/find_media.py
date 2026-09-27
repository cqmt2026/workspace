# -*- coding: utf-8 -*-
import os

paths_to_check = [
    r'C:\Users\Administrator\.openclaw',
    r'C:\Users\Administrator\AppData\Local\Temp',
]

for base in paths_to_check:
    if os.path.exists(base):
        print('检查:', base)
        for root, dirs, files in os.walk(base):
            media = [f for f in files if f.lower().endswith(('.png','.jpg','.jpeg','.gif','.webp'))]
            if media and len(media) > 0:
                print('  媒体文件在:', root)
                for f in media[:5]:
                    full = os.path.join(root, f)
                    print('   ', f, '=', os.path.getsize(full), 'bytes')
            # 找相关目录
            for d in dirs:
                if any(kw in d.lower() for kw in ['media', 'upload', 'temp', 'cache', 'image', 'photo']):
                    print('  相关目录:', os.path.join(root, d))
        print()
