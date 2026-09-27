# -*- coding: utf-8 -*-
"""
推送通知模块 — 标准化交付机制

设计原则：
1. 每个任务定义 output_format + delivery_level
2. 统一推送格式：标题 + 摘要 + 详情
3. 日志记录每次推送结果

用法:
    from scripts.notify import notify
    notify("持仓异常", "斯瑞新材 -12.87%", details=...)
"""
import os, json, sys
from datetime import datetime
from typing import Optional, Dict, Any

WORK_DIR = r"C:\Users\Administrator\.openclaw\workspace\workspace-investment"
LOG_DIR = os.path.join(WORK_DIR, "data")
os.makedirs(LOG_DIR, exist_ok=True)

DELIVERY_LOG = os.path.join(LOG_DIR, "delivery_log.json")

def load_delivery_log() -> list:
    if os.path.exists(DELIVERY_LOG):
        with open(DELIVERY_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_delivery_log(log: list):
    with open(DELIVERY_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def notify(
    title: str,
    summary: str,
    details: Optional[Dict[str, Any]] = None,
    level: str = "info",  # info / warning / alert
    task_name: Optional[str] = None,
    output_files: Optional[list] = None,
) -> Dict[str, Any]:
    """
    记录推送事件。
    实际推送由Cron的delivery配置触发，此函数负责：
    1. 记录交付日志
    2. 验证输出文件完整性
    3. 格式化推送内容

    返回: {"status": "ok|fail", "message": "..."}
    """
    result = {
        "status": "ok",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": title,
        "summary": summary,
        "level": level,
        "task_name": task_name,
    }

    # 验证输出文件
    missing_files = []
    if output_files:
        for fp in output_files:
            full_path = fp if os.path.isabs(fp) else os.path.join(WORK_DIR, fp)
            if not os.path.exists(full_path):
                missing_files.append(fp)

    if missing_files:
        result["status"] = "fail"
        result["message"] = f"输出文件缺失: {missing_files}"
    else:
        result["message"] = "交付正常"

    # 记录日志
    log = load_delivery_log()
    log.append(result)
    # 只保留最近30条
    if len(log) > 30:
        log = log[-30:]
    save_delivery_log(log)

    return result

def format_push_content(title: str, summary: str, details: Optional[Dict] = None) -> str:
    """格式化推送内容"""
    lines = [f"📋 {title}", ""]
    lines.append(summary)
    if details:
        lines.append("")
        lines.append("---")
        for k, v in details.items():
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)

def get_recent_deliveries(hours: int = 24) -> list:
    """获取最近N小时的交付记录"""
    log = load_delivery_log()
    cutoff = datetime.now()
    from datetime import timedelta
    cutoff = cutoff - timedelta(hours=hours)
    recent = []
    for entry in log:
        ts = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
        if ts >= cutoff:
            recent.append(entry)
    return recent
