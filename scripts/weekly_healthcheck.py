"""
weekly_healthcheck.py - 系统安全周检
每周一运行，执行 healthcheck skill 的读-only 检查并生成报告
"""
import subprocess
import os
import sys
import json
from datetime import datetime
import io

WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"
REPORT_DIR = os.path.join(WORKSPACE, "memory", "logs", "healthcheck")
os.makedirs(REPORT_DIR, exist_ok=True)

def run_check(name, cmd):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            timeout=30, encoding="utf-8", errors="ignore"
        )
        return {
            "name": name,
            "ok": result.returncode == 0,
            "stdout": result.stdout[:500] if result.stdout else "",
            "stderr": result.stderr[:200] if result.stderr else "",
        }
    except Exception as e:
        return {"name": name, "ok": False, "error": str(e)}

def main():
    date_str = datetime.now().strftime("%Y%m%d")
    report_path = os.path.join(REPORT_DIR, "healthcheck_" + date_str + ".md")

    checks = [
        ("Gateway进程", "tasklist | findstr node"),
        ("Cron任务数", "openclaw cron list"),
        ("Plugins数量", "openclaw plugins list"),
        ("Disk空间C", "powershell -Command \"Get-PSDrive C | Select-Object Used,Free | ConvertTo-Json\""),
        ("内存使用", "wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /format:list"),
    ]

    results = []
    for name, cmd in checks:
        r = run_check(name, cmd)
        results.append(r)

    ok_count = sum(1 for r in results if r.get("ok"))
    fail_count = len(results) - ok_count

    lines = [
        "# System Security Weekly Check - " + date_str,
        "**Time**: " + datetime.now().strftime("%Y-%m-%d %H:%M"),
        "",
        "## Check Results",
        "",
        "| Check | Status | Note |",
        "|------|--------|------|",
    ]
    for r in results:
        status = "OK" if r.get("ok") else "FAIL"
        note = r.get("error", "")[:50] or r.get("stderr", "")[:50] or "normal"
        lines.append("| " + r["name"] + " | " + status + " | " + note + " |")

    lines.extend([
        "",
        "## Summary",
        "- Total: " + str(len(results)),
        "- OK: " + str(ok_count),
        "- FAIL: " + str(fail_count),
        "",
    ])

    content = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("[healthcheck] Report: " + report_path)
    print("[healthcheck] Checks: " + str(len(results)) + ", Fails: " + str(fail_count))
    return report_path

if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()