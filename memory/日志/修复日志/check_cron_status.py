# -*- coding: utf-8 -*-
import urllib.request
import json

try:
    r = urllib.request.urlopen('http://127.0.0.1:18789/api/cron/list', timeout=10)
    d = json.loads(r.read())
    for job in d.get('jobs', []):
        state = job.get('state', {})
        print(f"{job['name']}: consecErr={state.get('consecutiveErrors', 0)} last={state.get('lastStatus', '')} reason={state.get('lastErrorReason', '')}")
except Exception as e:
    print(f"Error: {e}")
