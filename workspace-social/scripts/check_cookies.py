import json
from datetime import datetime

toutiao_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-social\config\toutiao_accounts.json'

with open(toutiao_path, 'r', encoding='utf-8') as f:
    raw = f.read()

# Try to fix encoding
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    # Fix mangled Chinese chars
    raw_fixed = raw.encode('utf-8').decode('utf-8')
    data = json.loads(raw_fixed)

accounts = data.get('accounts', [])
print(f"头条账号数: {len(accounts)}")
for acc in accounts:
    name = acc.get('name', 'N/A')
    status = acc.get('status', 'N/A')
    cookie = acc.get('credentials', {}).get('cookie', '')
    # Check sid_guard expiry
    sid_guard = ''
    for part in cookie.split(';'):
        if 'sid_guard' in part:
            sid_guard = part.strip()
    print(f"  名称: {name}")
    print(f"  状态: {status}")
    print(f"  sid_guard: {sid_guard[:80]}")
