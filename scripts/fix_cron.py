# -*- coding: utf-8 -*-
"""Fix cron jobs via gateway API"""
import json, sys, time
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import urllib.request

BASE = 'http://127.0.0.1:18789'
TOKEN = 'c321e1637183245af253b8bc817822170c1c65454627558c'

def call(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'Bearer {TOKEN}')
    req.add_header('Content-Type', 'application/json')
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return json.loads(r.read())
    except Exception as e:
        return {'error': str(e)}

# Get current config
print("Fetching config...")
r = call('GET', '/api/v1/config')
print(f"Config fetch: {list(r.keys()) if isinstance(r, dict) else type(r)}")

# Try to get cron jobs
print("\nFetching cron list...")
r2 = call('GET', '/api/v1/cron')
if 'jobs' in r2:
    print(f"Got {len(r2['jobs'])} jobs")
else:
    print(f"Cron response: {str(r2)[:200]}")
