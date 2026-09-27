"""
run_with_log.py - 通用Cron任务日志包装器

用法:
    python run_with_log.py <task_name> <system> <script_path> [args...]

示例:
    python run_with_log.py "Hot-Topic-Finder" "main" "scripts/hot_topic_find.py"

原理:
    在运行目标脚本前后自动记录开始/结束日志，
    目标脚本抛出异常时自动记录错误日志。
    无需修改任何原有脚本。
"""
import sys
import os
import json
import traceback
import subprocess
from datetime import datetime, timedelta

# 添加workspace路径
WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"
sys.path.insert(0, WORKSPACE)

from scripts.task_logger import log, LogTask
import io

# 熔断状态文件
FAILURE_STATE_FILE = os.path.join(WORKSPACE, "logs", "cron_failure_state.json")


def _load_failure_state():
    """加载熔断状态，失败时返回空字典。"""
    try:
        if os.path.exists(FAILURE_STATE_FILE):
            with open(FAILURE_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_failure_state(state):
    """保存熔断状态，失败时静默跳过。"""
    try:
        os.makedirs(os.path.dirname(FAILURE_STATE_FILE), exist_ok=True)
        with open(FAILURE_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _check_circuit_breaker(task_name):
    """
    检查熔断器状态。
    返回: ('run', 状态) 或 ('skip', 原因)
    """
    try:
        state = _load_failure_state()
        task_state = state.get(task_name, {})
        consecutive = task_state.get("consecutive_failures", 0)
        paused_until = task_state.get("paused_until")

        # 检查是否处于熔断暂停期
        if paused_until:
            try:
                pause_time = datetime.fromisoformat(paused_until)
                if datetime.now() < pause_time:
                    return ("skip", f"熔断中，暂停至 {paused_until}")
            except Exception:
                pass

        # 连续失败次数决定行为
        if consecutive >= 5:
            # 连续5次失败 → 熔断，暂停24h
            pause_time = datetime.now() + timedelta(hours=24)
            task_state["paused_until"] = pause_time.isoformat()
            state[task_name] = task_state
            _save_failure_state(state)
            return ("skip", f"连续{consecutive}次失败，熔断暂停至 {pause_time.isoformat()}")
        elif consecutive >= 3:
            return ("warn", f"连续{consecutive}次失败，注意")

        return ("run", "")
    except Exception:
        return ("run", "")


def _record_failure(task_name, success):
    """记录运行结果，更新熔断计数器。"""
    try:
        state = _load_failure_state()
        task_state = state.get(task_name, {"consecutive_failures": 0})

        if success:
            task_state["consecutive_failures"] = 0
            task_state.pop("paused_until", None)
        else:
            task_state["consecutive_failures"] = task_state.get("consecutive_failures", 0) + 1

        state[task_name] = task_state
        _save_failure_state(state)
    except Exception:
        pass

def run_with_log(task_name, system, script_path, extra_args=None):
    """包装运行一个脚本，自动记录日志（含熔断保护）"""

    # 熔断检查
    breaker_action, breaker_msg = _check_circuit_breaker(task_name)
    if breaker_action == "skip":
        print(f"[run] SKIP {task_name}: {breaker_msg}")
        return True  # 返回 True 避免 Cron 标记为失败
    elif breaker_action == "warn":
        print(f"[run] WARN {task_name}: {breaker_msg}")

    full_script = os.path.join(WORKSPACE, script_path)
    if not os.path.exists(full_script):
        # 尝试相对路径
        if os.path.exists(script_path):
            full_script = script_path

    if not os.path.exists(full_script):
        log(task_name, system, status="ERROR", error_msg=f"Script not found: {script_path}")
        print(f"[run] SCRIPT_NOT_FOUND: {full_script}")
        return False

    args = extra_args or []
    start_time = datetime.now()

    print(f"[run] START {task_name} ({system}) -> {script_path}")

    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        result = subprocess.run(
            [sys.executable, full_script] + args,
            capture_output=False,
            timeout=3600,
            encoding="utf-8", errors="replace",
            env=env
        )
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        if result.returncode == 0:
            log(task_name, system, status="OK", duration_ms=duration_ms,
                detail=f"Exit code: {result.returncode}")
            print(f"[run] OK {task_name} ({duration_ms:.0f}ms)")
            _record_failure(task_name, True)
            return True
        else:
            print(f"[run] FAIL {task_name} exit={result.returncode} ({duration_ms:.0f}ms)")
            _record_failure(task_name, False)
            return False

    except subprocess.TimeoutExpired:
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        log(task_name, system, status="ERROR",
            error_msg="Timeout after 600s", duration_ms=duration_ms)
        print(f"[run] TIMEOUT {task_name} after 600s")
        _record_failure(task_name, False)
        return False

    except Exception as e:
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        log(task_name, system, status="ERROR",
            error_msg=f"{type(e).__name__}: {e}",
            detail=traceback.format_exc(),
            duration_ms=duration_ms)
        print(f"[run] ERROR {task_name}: {type(e).__name__}: {e}")
        _record_failure(task_name, False)
        return False

if __name__ == "__main__":

    if len(sys.argv) < 4:
        print("用法: python run_with_log.py <task_name> <system> <script_path> [args...]")
        print("示例: python run_with_log.py Hot-Topic-Finder main scripts/hot_topic_find.py")
        sys.exit(1)

    task_name = sys.argv[1]
    system = sys.argv[2]
    script_path = sys.argv[3]
    extra_args = sys.argv[4:] if len(sys.argv) > 4 else None

    success = run_with_log(task_name, system, script_path, extra_args)
    sys.exit(0 if success else 1)