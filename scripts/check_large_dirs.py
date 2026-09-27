# -*- coding: utf-8 -*-
import os, sys

workspace = r'C:\Users\Administrator\.openclaw\workspace'
paths = [
    os.path.join(workspace, 'workspace-math', 'L4-共享'),
    os.path.join(workspace, 'workspace-math', 'L3-场景'),
    os.path.join(workspace, 'workspace-maphot'),
    os.path.join(workspace, 'backup'),
    os.path.join(workspace, 'workspace-math', 'archive'),
    os.path.join(workspace, 'workspace-math', 'assets'),
    os.path.join(workspace, 'workspace-math', 'media'),
]

for p in paths:
    if os.path.exists(p):
        total = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(p) for f in fs)
        label = p.replace(workspace, '').lstrip('\\')
        print(f'{label}: {total/1024**2:.0f}MB')
