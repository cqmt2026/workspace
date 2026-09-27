#!/usr/bin/env python3
import sys, os, subprocess, time
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TARGET = "o9cq8092w_2W-BHmLsGGbleQEHKg@im.wechat"
OPENCLAW = os.path.join(os.environ.get('APPDATA', ''), 'npm', 'openclaw.cmd')

if len(sys.argv) > 1:
    msg = sys.argv[1]
else:
    try:
        msg = sys.stdin.read()
    except:
        msg = ''

for i in range(3):
    try:
        r = subprocess.run([OPENCLAW, 'message', 'send', '--target', TARGET, '--message', msg],
                          capture_output=True, timeout=20,
                          env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONIOENCODING_OUT': 'utf-8'},
                          encoding='utf-8', errors='replace')
        if r.returncode == 0:
            print(f'[OK] Sent')
            sys.exit(0)
        time.sleep(2)
    except:
        time.sleep(2)
print('Failed')