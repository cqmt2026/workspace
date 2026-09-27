import json
import sys

logs = []
f = open(r'C:\Users\Administrator\.openclaw\workspace\memory\日志\task\2026\08\all\20260819.jsonl', 'r', encoding='utf-8')
for line in f:
    if line.strip():
        logs.append(json.loads(line))
f.close()

ok = [l for l in logs if l.get('status') == 'OK']
err = [l for l in logs if l.get('status') == 'ERROR']
skip = [l for l in logs if l.get('status') == 'SKIPPED']

print(f'Total: {len(logs)}, OK: {len(ok)}, Errors: {len(err)}, Skipped: {len(skip)}')
print()
print('=== ERRORS ===')
for l in err:
    task = l.get('task', 'unknown')
    system = l.get('system', 'unknown')
    duration = l.get('duration_ms', 0)
    error = l.get('error', '(none)')[:80]
    detail = l.get('detail', '')[:100]
    print(f'  {task} ({system}) - {duration:.0f}ms - error: {error} - detail: {detail}')

print()
print('=== OK ===')
for l in ok:
    task = l.get('task', 'unknown')
    system = l.get('system', 'unknown')
    duration = l.get('duration_ms', 0)
    print(f'  {task} ({system}) - {duration:.0f}ms')
