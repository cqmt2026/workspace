# -*- coding: utf-8 -*-
import os
from datetime import datetime

log_dir = r'C:\Users\Administrator\.openclaw\workspace\memory\日志'
if os.path.exists(log_dir):
    for f in sorted(os.listdir(log_dir)):
        fp = os.path.join(log_dir, f)
        if os.path.isfile(fp):
            mt = datetime.fromtimestamp(os.path.getmtime(fp))
            print(f'{mt.strftime("%m-%d %H:%M")} {f}')
        else:
            print(f'[DIR] {f}/')
