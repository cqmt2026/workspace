#!/usr/bin/env python3
"""Send WeChat message via openclaw CLI - standalone version"""
import sys, os, subprocess, time

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TARGET = "o9cq8092w_2W-BHmLsGGbleQEHKg@im.wechat"
OPENCLAW = os.path.join(os.environ.get('APPDATA', ''), 'npm', 'openclaw.cmd')

# Read message from file if no args
if len(sys.argv) > 1:
    msg = sys.argv[1]
else:
    msg_file = os.path.join(os.path.dirname(__file__), '..', 'out_data', 'daily_decision_latest.txt')
    try:
        with open(msg_file, 'r', encoding='utf-8') as f:
            msg = f.read()
    except:
        msg = ''

if not msg.strip():
    print('ERROR: empty message')
    sys.exit(1)

print(f'[DEBUG] Message length: {len(msg)} chars')
print(f'[DEBUG] OpenClaw path: {OPENCLAW}')
print(f'[DEBUG] Exists: {os.path.exists(OPENCLAW)}')

for i in range(3):
    try:
        result = subprocess.run(
            [OPENCLAW, 'message', 'send', '--target', TARGET, '--message', msg],
            capture_output=True,
            timeout=20,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
            encoding='utf-8',
            errors='replace'
        )
        print(f'[DEBUG] Attempt {i+1}: returncode={result.returncode}')
        print(f'[DEBUG] stdout: {result.stdout[:300] if result.stdout else "None"}')
        print(f'[DEBUG] stderr: {result.stderr[:500] if result.stderr else "None"}')
        if result.returncode == 0:
            print('[OK] Message sent successfully')
            sys.exit(0)
        time.sleep(2)
    except subprocess.TimeoutExpired:
        print(f'[WARN] Attempt {i+1} timeout')
        time.sleep(2)
    except Exception as e:
        print(f'[WARN] Attempt {i+1} error: {e}')
        time.sleep(2)

print('[FAIL] All attempts exhausted')
sys.exit(1)
