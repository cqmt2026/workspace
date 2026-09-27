# -*- coding: utf-8 -*-
import os, json, glob, datetime

print("=" * 50)
print("System Maintenance Check - 2026-08-21 19:43")
print("=" * 50)

# 1. Check fix logs
fix_logs = glob.glob(r'C:\Users\Administrator\.openclaw\workspace\memory\日志\修复日志\fix_*.md')
print(f"\nFix logs: {len(fix_logs)} total")
for f in sorted(fix_logs)[-5:]:
    mtime = os.path.getmtime(f)
    dt = datetime.datetime.fromtimestamp(mtime)
    sz = os.path.getsize(f)
    print(f"  {dt.strftime('%m-%d')} {os.path.basename(f)} ({sz}B)")

# 2. Check shared knowledge
sk_path = r'C:\Users\Administrator\.openclaw\workspace\shared-knowledge'
if os.path.exists(sk_path):
    files = os.listdir(sk_path)
    print(f"\nShared knowledge: {len(files)} files")

# 3. Memory system
memory_dirs = {
    'memory/': r'C:\Users\Administrator\.openclaw\workspace\memory',
    'memory/系统/': r'C:\Users\Administrator\.openclaw\workspace\memory\系统',
    'memory/日志/': r'C:\Users\Administrator\.openclaw\workspace\memory\日志',
    'memory/日志/修复日志/': r'C:\Users\Administrator\.openclaw\workspace\memory\日志\修复日志',
}
print("\nMemory structure:")
for name, path in memory_dirs.items():
    if os.path.exists(path):
        count = len(os.listdir(path))
        print(f"  {name}: {count} items")
    else:
        print(f"  {name}: MISSING")

# 4. Check Supermemory
sm_path = r'C:\Users\Administrator\.openclaw\workspace\memory\系统\supermemory'
if os.path.exists(sm_path):
    dbs = os.listdir(sm_path)
    print(f"\nSupermemory DBs: {len(dbs)}")
    for db in dbs:
        db_path = os.path.join(sm_path, db)
        if os.path.isdir(db_path):
            count = len(os.listdir(db_path))
            print(f"  {db}: {count} files")

# 5. Check recent maintenance log trends
log_path = r'C:\Users\Administrator\.openclaw\workspace\logs\system_maintenance.json'
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    total = len(lines)
    failures = 0
    for line in lines:
        try:
            data = json.loads(line.strip())
            rate = data.get('success_rate', '')
            if '/' in rate:
                ok, tot = map(int, rate.split('/'))
                if ok < tot:
                    failures += 1
        except:
            pass
    print(f"\nMaintenance log: {total} entries, {failures} failures, {(total-failures)/max(total,1)*100:.1f}% success")

# 6. Check cron failure state
cron_path = r'C:\Users\Administrator\.openclaw\workspace\logs\cron_failure_state.json'
if os.path.exists(cron_path):
    with open(cron_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"\nCron failure state:")
    for k, v in data.items():
        print(f"  {k}: {v}")

# 7. Check disk space
import shutil
total, used, free = shutil.disk_usage('C:\\')
print(f"\nDisk C: total={total//(1024**3)}GB used={used//(1024**3)}GB free={free//(1024**3)}GB ({free/total*100:.1f}%)")

print("\n" + "=" * 50)
print("Check complete")
print("=" * 50)
