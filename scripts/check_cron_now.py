import urllib.request, json, sys, time
t0 = time.time()
try:
    r = urllib.request.urlopen('http://127.0.0.1:18789/api/v1/cron', timeout=10)
    data = json.loads(r.read())
    jobs = data.get('jobs', [])
    errs = [j for j in jobs if j.get('status') == 'error']
    print(f'=== Cron Status {time.strftime("%Y-%m-%d %H:%M:%S")} ===')
    print(f'Total: {len(jobs)}  OK: {len(jobs)-len(errs)}  ERROR: {len(errs)}')
    for j in errs[:25]:
        name = j.get('name', '?')[:45]
        ec = j.get('errorCount', 0)
        phase = j.get('lastErrorPhase', '')
        reason = str(j.get('lastErrorReason', ''))[:60]
        print(f'  [{ec}x] {name} | phase={phase} | {reason}')
except Exception as e:
    print(f'API error: {e}')
