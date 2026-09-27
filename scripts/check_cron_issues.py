# -*- coding: utf-8 -*-
"""Check cron jobs for consecutive errors"""
import subprocess, json, sys

result = subprocess.run(
    ['openclaw', 'cron', 'list', '--json'],
    capture_output=True, text=True, timeout=15,
    cwd=r'C:\Users\Administrator\.openclaw\workspace'
)
data = json.loads(result.stdout)
jobs = data.get('jobs', [])
issues = [j for j in jobs if j.get('state', {}).get('consecutiveErrors', 0) >= 2]
print(f'Total jobs: {len(jobs)}, Issues (consecutiveErrors>=2): {len(issues)}')
for j in issues:
    s = j.get('state', {})
    print(f"  [{j.get('name')}]: {s.get('consecutiveErrors')} errors | status={j.get('status')} | lastError={s.get('lastError', 'N/A')} | delivery={s.get('lastDeliveryStatus', 'N/A')}")

# Also check Baidu-Monthly and Math-Cleanup specifically
for name in ['Baidu-月度汇总', 'Math-Cleanup-每月清理临时文件']:
    found = [j for j in issues if j.get('name') == name]
    if found:
        j = found[0]
        s = j.get('state', {})
        print(f"\n  === {name} ===")
        print(f"    consecutiveErrors: {s.get('consecutiveErrors')}")
        print(f"    lastError: {s.get('lastError')}")
        print(f"    lastDeliveryStatus: {s.get('lastDeliveryStatus')}")
        print(f"    lastFailureNotificationDeliveryStatus: {s.get('lastFailureNotificationDeliveryStatus')}")
