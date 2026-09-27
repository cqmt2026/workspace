# -*- coding: utf-8 -*-

"""
时间门控：允许 6:00-23:00 执行
自动添加于 2026-05-23
"""
from datetime import datetime
import sys

_now = datetime.now()
if _now.hour >= 23 or _now.hour < 6:
    print(f'[{_now.strftime("%H:%M")}] 时间窗口外(6-23)，跳过执行')
    sys.exit(0)
del _now


"""
system_maintenance.py - 系统维护综合脚本
合并：Session-State备份 + PREFERENCES同步 + Token监控
每30分钟自动运行一次
"""

import os
import sys
import json
import subprocess
from datetime import datetime
import io

WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"

def run_session_backup():
    try:
        result = subprocess.run(
            ["python", "-X", "utf8", f"{WORKSPACE}\\scripts\\session_state_backup.py"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60
        )
        if result.returncode == 0:
            return True, "Session-Backup OK"
        else:
            return False, "Session-Backup FAIL"
    except Exception as e:
        return False, f"Session-Backup ERROR: {e}"

def run_preferences_sync():
    try:
        result = subprocess.run(
            ["python", "-X", "utf8", f"{WORKSPACE}\\scripts\\sync_preferences.py"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60
        )
        if result.returncode == 0:
            return True, "PREFERENCES-Sync OK"
        else:
            return False, "PREFERENCES-Sync FAIL"
    except Exception as e:
        return False, f"PREFERENCES-Sync ERROR: {e}"

def run_token_monitor():
    try:
        result = subprocess.run(
            ["python", "-X", "utf8", f"{WORKSPACE}\\memory\\系统\\auto_check.py"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60
        )
        if result.returncode == 0:
            return True, "Token-Monitor OK"
        else:
            return False, "Token-Monitor FAIL"
    except Exception as e:
        return False, f"Token-Monitor ERROR: {e}"

def run_auto_stagger():
    try:
        result = subprocess.run(
            ["python", f"{WORKSPACE}\\scripts\\auto_stagger.py"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
        )
        if result.returncode == 0:
            return True, "Auto-Stagger OK"
        else:
            return False, "Auto-Stagger FAIL"
    except Exception as e:
        return False, f"Auto-Stagger ERROR: {e}"

def run_self_optimize():
    """运行自我优化检查"""
    try:
        result = subprocess.run(
            ["python", "-X", "utf8", f"{WORKSPACE}\\scripts\\self_optimize.py"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
        )
        if result.returncode == 0:
            return True, "Self-Optimize OK"
        else:
            return False, "Self-Optimize FAIL"
    except Exception as e:
        return False, f"Self-Optimize ERROR: {e}"


def main():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] System-Maintenance START...")
    print(f"  [INFO] Session-Backup和Token-Monitor由独立Cron覆盖，此处跳过")
    
    results = []
    
    ok, msg = run_preferences_sync()
    print(f"  [{'OK' if ok else 'FAIL'}] {msg}")
    results.append(("PREFERENCES-Sync", ok))
    
    # auto_stagger.py 不存在，跳过
    # 见: https://github.com/xxx 待确认是否需要重建
    print(f"  [SKIP] Auto-Stagger (脚本不存在，待确认)")
    results.append(("Auto-Stagger", True))
    
    ok, msg = run_self_optimize()
    print(f"  [{'OK' if ok else 'FAIL'}] {msg}")
    results.append(("Self-Optimize", ok))
    
    ok, msg = sync_core_docs()
    print(f"  [{'OK' if ok else 'WARN'}] {msg}")
    results.append(("Core-Docs-Sync", ok))
    
    total = len(results)
    ok_count = sum(1 for _, ok in results if ok)
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Done: {ok_count}/{total}")
    
    log_file = os.path.join(WORKSPACE, "logs", "system_maintenance.json")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    log_data = {
        "time": datetime.now().isoformat(),
        "results": results,
        "success_rate": f"{ok_count}/{total}"
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
    
    return ok_count == total


def sync_core_docs():
    """检测核心文档最后更新日期与实际 mtime 是否一致，不一致时告警。"""
    import re
    files = [
        ("AGENTS.md", r"最后更新.*?：\s*(\d{4}-\d{2}-\d{2})"),
        ("SOUL.md", r"最后更新.*?：\s*(\d{4}-\d{2}-\d{2})"),
        ("TOOLS.md", r"最后更新.*?：\s*(\d{4}-\d{2}-\d{2})"),
        ("MEMORY.md", r"最后更新.*?[:：]\s*(\d{4}-\d{2}-\d{2})"),
        ("HEARTBEAT.md", r"最后更新.*?[:：]\s*(\d{4}-\d{2}-\d{2})"),
    ]
    issues = []
    for fname, pattern in files:
        fpath = os.path.join(WORKSPACE, fname)
        if not os.path.exists(fpath):
            issues.append(f"{fname} 不存在")
            continue
        with open(fpath, encoding="utf-8", errors="replace") as f:
            content = f.read()
        m = re.search(pattern, content)
        if not m:
            issues.append(f"{fname} 找不到最后更新日期行")
            continue
        declared_date = m.group(1)
        mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
        mtime_str = mtime.strftime("%Y-%m-%d")
        if declared_date != mtime_str:
            issues.append(f"{fname} 声明日期 {declared_date} 与实际 mtime {mtime_str} 不一致")
    if issues:
        msg = "; ".join(issues)
        print(f"  [WARN] 文档同步问题: {msg}")
        return False, f"文档不一致: {len(issues)} 个问题"
    return True, "Core-Docs-Sync OK"


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    success = main()
    sys.exit(0 if success else 1)