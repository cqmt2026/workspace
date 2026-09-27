#!/usr/bin/env python3
import sys, os, subprocess, time

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TARGET = "o9cq8092w_2W-BHmLsGGbleQEHKg@im.wechat"

# Find openclaw executable
openclaw_paths = [
    os.path.join(os.environ.get('APPDATA', ''), 'npm', 'openclaw.cmd'),
    'openclaw',
    'C:\\Users\\Administrator\\AppData\\Roaming\\npm\\openclaw.cmd',
]

openclaw = None
for p in openclaw_paths:
    if os.path.exists(p):
        openclaw = p
        break

if not openclaw:
    print('ERROR: openclaw executable not found')
    sys.exit(1)

if len(sys.argv) > 1:
    msg = sys.argv[1]
else:
    try:
        msg = sys.stdin.read()
    except:
        msg = ''

if not msg.strip():
    print('ERROR: empty message')
    sys.exit(1)

print(f'[DEBUG] Using openclaw: {openclaw}')
print(f'[DEBUG] Target: {TARGET}')
print(f'[DEBUG] Message length: {len(msg)}')

for i in range(3):
    try:
        r = subprocess.run(
            [openclaw, 'message', 'send', '--target', TARGET, '--message', msg],
            capture_output=True, timeout=25,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
            encoding='utf-8', errors='replace'
        )
        print(f'[DEBUG] Attempt {i+1}: returncode={r.returncode}')
        print(f'[DEBUG] stdout: {r.stdout[:200] if r.stdout else "None"}')
        print(f'[DEBUG] stderr: {r.stderr[:500] if r.stderr else "None"}')
        if r.returncode == 0:
            print('[OK] Sent')
            sys.exit(0)
        time.sleep(2)
    except Exception as e:
        print(f'[DEBUG] Attempt {i+1} error: {e}')
        time.sleep(2)

print('Failed')
sys.exit(1)
