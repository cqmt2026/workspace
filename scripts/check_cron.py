import json, subprocess

openclaw_exe = r'C:\Users\Administrator\AppData\Roaming\npm\openclaw.cmd'
result = subprocess.run([openclaw_exe, 'cron', 'list', '--json'], capture_output=True, timeout=30)
stdout = result.stdout.decode('utf-8', errors='replace')
data = json.loads(stdout)

print(f"total: {data.get('total')}")
print(f"hasMore: {data.get('hasMore')}")
jobs = data.get('jobs', [])
print(f"jobs count: {len(jobs)}")
enabled = [j for j in jobs if j.get('enabled', True)]
disabled = [j for j in jobs if not j.get('enabled', True)]
print(f"enabled: {len(enabled)}, disabled: {len(disabled)}")
print("\nEnabled jobs:")
for j in sorted(enabled, key=lambda x: x['name']):
    print(f"  {j['name']}")
print(f"\nDisabled jobs ({len(disabled)}):")
for j in sorted(disabled, key=lambda x: x['name']):
    print(f"  {j['name']}")
