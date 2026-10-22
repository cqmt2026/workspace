# -*- coding: utf-8 -*-
"""
Task Logger - Cron任务日志记录
提供 log() 和 LogTask 供 run_with_log.py 使用
"""
import os
import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(r"C:\Users\Administrator\.openclaw\workspace\logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

CRON_LOG_FILE = LOG_DIR / "cron_log.jsonl"


def log(task_name, system, status="OK", error_msg=None, detail=None, duration_ms=None):
    """
    记录一条cron任务日志
    
    Args:
        task_name: 任务名称
        system: 系统标识 (如 main)
        status: 状态 (OK / ERROR)
        error_msg: 错误信息
        detail: 详细信息
        duration_ms: 执行耗时(ms)
    """
    entry = {
        "ts": datetime.now().isoformat(),
        "task": task_name,
        "system": system,
        "status": status,
        "duration_ms": duration_ms,
    }
    if error_msg:
        entry["error"] = error_msg
    if detail:
        entry["detail"] = detail

    try:
        with open(CRON_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


class LogTask:
    """上下文管理器，自动记录任务开始/结束"""
    
    def __init__(self, task_name, system):
        self.task_name = task_name
        self.system = system
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        log(self.task_name, self.system, status="START")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000 if self.start_time else 0
        if exc_type:
            log(self.task_name, self.system, status="ERROR",
                error_msg=f"{exc_type.__name__}: {exc_val}",
                duration_ms=duration_ms)
        else:
            log(self.task_name, self.system, status="OK",
                duration_ms=duration_ms)
        return False
