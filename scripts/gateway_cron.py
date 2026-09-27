import urllib.request, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')
WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'
# Try Gateway REST API with correct path
paths = ['/api/cron', '/api/v1/cron', '/cron', '/api/jobs', '/api/v1/jobs']
for path in paths:
    try:
        r = urllib.request.urlopen(f'http://127.0.0.1:18789{path}', timeout=8)
        data = json.loads(r.read())
        print(f'Path {path} works')
        jobs = data if isinstance(data, list) else data.get('jobs', [])
        print(f'Got {len(jobs)} jobs')
        errs = [j for j in jobs if str(j.get('state',{}).get('lastStatus',''))=='error']
        print(f'Error: {len(errs)}')
        for j in errs[:15]:
            name = j.get('name','?')
            state = j.get('state',{})
            ce = state.get('consecutiveErrors',0)
            ls = state.get('lastStatus','')
            print(f'  {name} | ce={ce} | status={ls}')
        break
    except Exception as e:
        print(f'{path}: {e}')
print('Done')
