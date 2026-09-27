# -*- coding: utf-8 -*-
import io
import os, sys, subprocess, winreg

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# 读取Machine级MX_APIKEY
try:
    key = winreg.QueryValueEx(
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0),
        'MX_APIKEY'
    )[0]
except:
    key = os.environ.get('MX_APIKEY', '')

env = os.environ.copy()
env['MX_APIKEY'] = key

print(f'MX_APIKEY: {"已设置" if key else "未设置"}')
print('启动ML训练...')

result = subprocess.run(
    [sys.executable,
     r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\quant_ml\main.py',
     '--exp', 'quant_ml_v1'],
    env=env,
    capture_output=False
)
print(f'退出码: {result}')
