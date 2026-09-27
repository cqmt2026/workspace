# -*- coding: utf-8 -*-
import os, json, subprocess
from datetime import datetime

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'
LOG_DIR = os.path.join(WORKSPACE, 'memory', '日志', '修复日志')

print(f"[L1] Self-Heal Check at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 40)

issues = []
log_errors = []

# 1. Cron jobs status
try:
    result = subprocess.run(
        ['openclaw', 'cron', 'list', '--json'],
        capture_output=True, text=True, timeout=30,
        cwd=WORKSPACE
    )
    data = json.loads(result.stdout) if result.stdout else {}
    jobs = data.get('jobs', [])
    print(f"\n[Cron Jobs] Total: {len(jobs)}")
    issues = []
    for j in jobs:
        name = j.get('name', '未知')
        enabled = j.get('enabled', False)
        state = j.get('state', {})
        errors = state.get('consecutiveErrors', 0)
        last_status = state.get('lastStatus', 'n/a')
        last_run = state.get('lastRunAtMs', 0)
        run_time = datetime.fromtimestamp(last_run/1000).strftime('%m-%d %H:%M') if last_run else 'never'
        print(f"  {'✅' if enabled else '❌'} {name}: enabled={enabled}, errors={errors}, last={last_status} ({run_time})")
        if errors >= 2 and enabled:
            issues.append(f"{name}: {errors} consecutive errors, last={last_status}")
except Exception as e:
    print(f"[ERROR] Cron list: {e}")
    issues.append(f"Cron list error: {e}")

# 2. Recent error logs
today = datetime.now().strftime('%Y%m%d')
log_file = os.path.join(WORKSPACE, 'memory', '日志', 'task', today[:4], today[4:6], 'all', f'{today}.jsonl')
log_errors = []
if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get('status') == 'error':
                    log_errors.append(f"{entry.get('task','?')}: {str(entry.get('error',''))[:60]}")
            except: pass
    print(f"\n[Today's Logs] {today}: {len(log_errors)} errors")
    for e in log_errors[:5]:
        print(f"  ❌ {e}")
else:
    print(f"\n[Today's Logs] {today}: no log file")

# 3. Check recent fix logs for patterns
recent_fixes = []
if os.path.exists(LOG_DIR):
    files = sorted(os.listdir(LOG_DIR), reverse=True)[:10]
    recent_fixes = [f for f in files if f.startswith('fix_')]
    print(f"\n[Recent Fixes] Last 10: {len(recent_fixes)} fix logs")
    for f in recent_fixes[:5]:
        print(f"  📄 {f}")

# 4. Disk space check
try:
    import shutil
    total, used, free = shutil.disk_usage(WORKSPACE.rpartition('\\', 1)[0])
    print(f"\n[Disk] Total: {total//1024**3}GB, Used: {used//1024**3}GB, Free: {free//1024**3}GB")
except: pass

# Summary
all_issues = issues + log_errors
if not all_issues:
    print("\n[PASS] 无异常任务")
    exit(0)
else:
    print(f"\n[ALERT] 发现 {len(all_issues)} 个异常:")
    for i in all_issues:
        print(f"  ⚠️ {i}")
    exit(1)
