# -*- coding: utf-8 -*-
"""L1 Monitor - analyze cron jobs for errors"""
import json, subprocess, re, sys, os
from datetime import datetime

# Fix Windows GBK encoding issue
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'
LOG_DIR = os.path.join(WORKSPACE, 'memory', '日志', '修复日志')
os.makedirs(LOG_DIR, exist_ok=True)

KNOWN_ISSUES = {
    'Hot-Topic-Finder': 'sensenova billing error, 等待充值验证',
    'Web-Hot-全网热点': 'sensenova billing error, 同上',
    'Pre-Market-Check-开盘前预检': 'timeout 7次，需检查脚本逻辑',
}

def run_cron_list():
    try:
        r = subprocess.run(['cmd', '/c', 'openclaw', 'cron', 'list', '--json'],
                          capture_output=True, timeout=15, cwd=WORKSPACE)
        text = r.stdout.decode('utf-8', errors='replace') + r.stderr.decode('utf-8', errors='replace')
        m = re.search(r'\{', text)
        if m:
            return json.loads(text[m.start():])
    except Exception as e:
        print(f"[WARN] cron list failed: {e}")
    return {'jobs': []}

def main():
    jobs_data = run_cron_list()
    jobs = jobs_data.get('jobs', [])
    print(f"[L1] Check at {datetime.now().strftime('%Y-%m-%d %H:%M')} | Total: {len(jobs)}")

    ok = err = idle = 0
    error_jobs = []
    for j in jobs:
        st = j.get('state', {}).get('lastStatus', '')
        ce = j.get('state', {}).get('consecutiveErrors', 0)
        if st == 'ok': ok += 1
        elif st == 'error':
            err += 1
            error_jobs.append(j)
        elif st == 'idle': idle += 1

    print(f"  Status: OK={ok}  ERROR={err}  IDLE={idle}")

    issues = []
    for j in error_jobs:
        name = j.get('name', '?')
        state = j.get('state', {})
        ce = state.get('consecutiveErrors', 0)
        err_reason = state.get('lastError', '') or state.get('lastDiagnosticSummary', '')
        diag = state.get('lastDiagnostics', {})
        summary = diag.get('summary', '') if isinstance(diag, dict) else ''
        reason = err_reason or summary

        if ce >= 2:
            known = KNOWN_ISSUES.get(name)
            if known:
                print(f"  SKIP known: {name} ({known})")
                continue
            issues.append({'name': name, 'errors': ce, 'reason': reason[:200]})

    if not issues:
        print("[PASS] No new unhandled errors (>=2 consecutive)")
        return 0

    print(f"\n[ALERT] {len(issues)} unhandled error jobs:")
    alert_lines = [f"L1 Monitor found {len(issues)} error jobs (>=2 consecutive errors):"]
    for i in issues:
        msg = f"  {i['name']}: {i['reason']}"
        print(msg, file=sys.stdout)
        alert_lines.append(f"- {i['name']}: {i['reason']}")

    alert_text = '\n'.join(alert_lines) + f'\n--- L1 Monitor {datetime.now().strftime("%H:%M")} ---'
    report = os.path.join(LOG_DIR, f'l1_alert_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
    with open(report, 'w', encoding='utf-8') as f:
        f.write(alert_text)
    print(f'\n  Report: {report}')
    # NOTE: Always return 0. Returning 1 when errors found causes run_with_log to
    # treat the monitor itself as failed, creating a false-positive failure cascade.
    return 0

if __name__ == '__main__':
    sys.exit(main())