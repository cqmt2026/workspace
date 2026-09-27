"""
task_logger.py - 统一任务日志模块
所有主系统/子系统任务必须通过此模块记录日志

用法:
    from task_logger import log_task

    # 方式1: 装饰器（推荐）
    @log_task(system="main", task_name="Hot-Topic-Finder")
    def my_task():
        ...

    # 方式2: 上下文管理器
    with log_task("strategy_scan", "investment"):
        run_strategy()
"""
import os
import json
import traceback
from datetime import datetime
from functools import wraps
import io

# ============================================================
# 配置
# ============================================================
LOG_BASE = r"C:\Users\Administrator\.openclaw\workspace\memory\日志\task"

SYSTEMS = ["main", "novel", "investment", "social", "math", "weixin"]
STATUS_OK = "OK"
STATUS_ERROR = "ERROR"
STATUS_SKIPPED = "SKIPPED"

# ============================================================
# 工具函数
# ============================================================
def get_log_path(date_str=None, system=None):
    """获取日志文件路径。date_str格式: YYYYMMDD"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    d = date_str
    y = d[:4]
    m = d[4:6]

    if system:
        # 按系统分目录
        base = os.path.join(LOG_BASE, y, m, system)
    else:
        # 汇总日志（所有系统）
        base = os.path.join(LOG_BASE, y, m, "all")

    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{date_str}.jsonl")

def ensure_log_dir():
    """确保日志根目录存在"""
    os.makedirs(LOG_BASE, exist_ok=True)

def append_log(record):
    """追加一条日志记录到当日文件"""
    ensure_log_dir()
    date_str = datetime.now().strftime("%Y%m%d")
    log_path = get_log_path(date_str, "all")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def write_system_log(system, date_str, records):
    """为指定系统写入专属日志（JSONL，每行一条）"""
    ensure_log_dir()
    log_path = get_log_path(date_str, system)
    with open(log_path, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

# ============================================================
# 核心日志函数
# ============================================================
def log(
    task_name,
    system,
    status=STATUS_OK,
    error_msg=None,
    detail=None,
    duration_ms=None,
    extra=None
):
    """
    记录一条任务执行日志。

    参数:
        task_name: 任务名称（如 "Hot-Topic-Finder"）
        system: 系统名（main/novel/investment/social/math/weixin）
        status: OK / ERROR / SKIPPED
        error_msg: 错误信息（可选）
        detail: 额外描述（可选）
        duration_ms: 执行时长毫秒（可选）
        extra: 其他自定义字段（可选，dict）
    """
    record = {
        "task": task_name,
        "system": system,
        "timestamp": datetime.now().isoformat(),
        "status": status,
    }
    if error_msg:
        record["error"] = error_msg
    if detail:
        record["detail"] = detail
    if duration_ms is not None:
        record["duration_ms"] = duration_ms
    if extra:
        record.update(extra)

    append_log(record)
    return record

# ============================================================
# 上下文管理器
# ============================================================
class LogTask:
    """上下文管理器 + 装饰器，支持嵌套"""
    _stack = []  # 支持嵌套调用

    def __init__(self, task_name, system, detail=None):
        self.task_name = task_name
        self.system = system
        self.detail = detail
        self.start_time = None
        self.error = None

    def __enter__(self):
        self.start_time = datetime.now()
        LogTask._stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        popped = LogTask._stack.pop() if LogTask._stack else None
        duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000

        if exc_type is not None:
            error_msg = f"{exc_type.__name__}: {exc_val}"
            detail = traceback.format_exc()
            log(
                task_name=self.task_name,
                system=self.system,
                status=STATUS_ERROR,
                error_msg=error_msg,
                detail=detail,
                duration_ms=duration_ms
            )
        else:
            log(
                task_name=self.task_name,
                system=self.system,
                status=STATUS_OK,
                detail=self.detail,
                duration_ms=duration_ms
            )
        return True  # 吞掉异常，不向外传播

    def set_detail(self, detail):
        self.detail = detail

def log_task(task_name=None, system="main", detail=None):
    """
    装饰器/工厂函数。
    用法:
        @log_task("my_task", "main")
        def my_task():
            ...
    """
    def decorator(func):
        _task_name = task_name or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            with LogTask(_task_name, system, detail=detail):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# ============================================================
# 读取日志
# ============================================================
def read_today_logs(system=None):
    """读取今日所有日志，或指定系统的日志"""
    date_str = datetime.now().strftime("%Y%m%d")
    return read_logs(date_str, system)

def read_logs(date_str, system=None):
    """读取指定日期的日志"""
    log_path = get_log_path(date_str, system)
    if not os.path.exists(log_path):
        return []

    records = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records

def list_log_dates(year=None, month=None):
    """列出有日志的日期列表"""
    if year and month:
        base = os.path.join(LOG_BASE, str(year), str(month).zfill(2))
    else:
        # 返回所有年份/月份
        base = LOG_BASE

    if not os.path.exists(base):
        return []

    dates = set()
    for root, dirs, files in os.walk(base):
        for fn in files:
            if fn.endswith(".jsonl"):
                dates.add(fn.replace(".jsonl", ""))
    return sorted(dates)

# ============================================================
# 命令行接口（被Cron任务调用）
# ============================================================
if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    import sys

    if len(sys.argv) < 3:
        print("用法: python task_logger.py <task_name> <system> [detail]")
        print("示例: python task_logger.py Hot-Topic-Finder main 'Found 5 topics'")
        sys.exit(1)

    task_name = sys.argv[1]
    system = sys.argv[2]
    detail = sys.argv[3] if len(sys.argv) > 3 else None

    with LogTask(task_name, system, detail=detail):
        pass  # 日志已记录