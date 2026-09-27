# -*- coding: utf-8 -*-
import subprocess, os, sys

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'
os.chdir(WORKSPACE)

try:
    r = subprocess.run(
        ['openclaw.cmd', 'gateway', 'status'],
        capture_output=True, timeout=15,
        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
        text=True, encoding='utf-8'
    )
    if r.stdout:
        print(r.stdout.strip()[:600])
    else:
        print("No stdout, stderr: %s" % (r.stderr.strip()[:200] if r.stderr else 'empty'))
except Exception as e:
    print("Error: %s" % e)
