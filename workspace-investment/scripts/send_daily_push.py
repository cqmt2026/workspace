# -*- coding: utf-8 -*-
import subprocess, os, sys, time
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

msg = open(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\daily_decision_2026-09-05.txt', encoding='utf-8').read()
target = 'o9cq8092w_2W-BHmLsGGbleQEHKg@im.wechat'
openclaw = os.path.join(os.environ.get('APPDATA', ''), 'npm', 'openclaw.cmd')

print(f'openclaw: {openclaw}')
print(f'msg len: {len(msg)}')

for i in range(3):
    try:
        r = subprocess.run([openclaw, 'message', 'send', '--target', target, '--message', msg],
                          capture_output=True, timeout=25,
                          env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONIOENCODING_OUT': 'utf-8'},
                          encoding='utf-8', errors='replace')
        print(f'Retry {i+1}: RC={r.returncode}')
        if r.stdout: print(f'OUT: {r.stdout[:300]}')
        if r.stderr: print(f'ERR: {r.stderr[:300]}')
        if r.returncode == 0:
            print('[OK] Sent')
            sys.exit(0)
        time.sleep(3)
    except Exception as e:
        print(f'Exception: {e}')
        time.sleep(3)
print('Failed after 3 retries')
