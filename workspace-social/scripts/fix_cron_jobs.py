import json
import shutil
import os

src = r'C:\Users\Administrator\.openclaw\cron\jobs.json.bak'
dst = r'C:\Users\Administrator\.openclaw\cron\jobs.json'
tmp = r'C:\Users\Administrator\.openclaw\cron\jobs.json.bak.fixed'

print(f"Reading: {src}")
with open(src, 'r', encoding='utf-8') as f:
    data = json.load(f)

jobs = data['jobs']
print(f"Total jobs: {len(jobs)}")

# Validate each job has required fields
valid_jobs = []
for j in jobs:
    required = ['id', 'name', 'enabled', 'schedule', 'sessionTarget', 'payload', 'delivery']
    if all(k in j for k in required):
        valid_jobs.append(j)
    else:
        print(f"  SKIP (incomplete): {j.get('name', 'unknown')}")

print(f"Valid jobs: {len(valid_jobs)}")

# Build clean jobs array
output = {'version': 1, 'jobs': valid_jobs}

with open(tmp, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

shutil.move(tmp, dst)
print(f"Written: {dst}")

# Verify
with open(dst, 'r', encoding='utf-8') as f:
    verify = json.load(f)
print(f"Verified jobs count: {len(verify['jobs'])}")
