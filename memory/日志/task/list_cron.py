import subprocess, json

openclaw_exe = r'C:\Users\Administrator\AppData\Roaming\npm\openclaw.cmd'
result = subprocess.run([openclaw_exe, 'cron', 'list', '--json'], capture_output=True, timeout=30)
stdout = result.stdout.decode('utf-8', errors='replace')
data = json.loads(stdout)
jobs = data.get('jobs', [])

enabled_jobs = [j for j in jobs if j.get('enabled', True)]
print(f'Total cron jobs: {len(jobs)}, Enabled: {len(enabled_jobs)}')
print()
for j in enabled_jobs:
    name = j.get('name', '')
    st = j.get('sessionTarget', 'main')
    print(f'  {name} (sessionTarget={st})')
