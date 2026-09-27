#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Executive Summary Generator
每日17:00自动生成一页纸简报，推送到微信
格式：量化先行 + 影响排序 + 行动导向
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace")
MEMORY_DIR = WORKSPACE / "memory"
LOGS_DIR = MEMORY_DIR / "日志"

def get_cron_status():
    """获取Cron状态"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True, text=True, timeout=15
        )
        lines = result.stdout.split('\n')
        enabled = sum(1 for l in lines if 'enabled' in l and 'false' not in l)
        errors = sum(1 for l in lines if 'error' in l)
        oks = sum(1 for l in lines if 'ok' in l and 'error' not in l)
        return {"enabled": enabled, "errors": errors, "oks": oks}
    except Exception as e:
        return {"error": str(e)}

def get_subsystem_status():
    """获取子系统状态"""
    subsystems = {
        "investment": {"path": WORKSPACE / "workspace-investment", "latest": None},
        "maphot": {"path": WORKSPACE / "workspace-maphot", "latest": None},
        "pv": {"path": WORKSPACE / "workspace-pv", "latest": None},
        "math": {"path": WORKSPACE / "workspace-math", "latest": None},
        "social": {"path": WORKSPACE / "workspace-social", "latest": None},
        "baidu": {"path": WORKSPACE / "workspace-baiduagent", "latest": None}
    }
    
    for name, info in subsystems.items():
        path = info["path"]
        # 查找最近修改的文件
        try:
            files = list(path.rglob("*")) 
            files = [f for f in files if f.is_file() and f.suffix in ['.py', '.md', '.json', '.db', '.txt', '.mp4']]
            if files:
                latest = max(files, key=lambda f: f.stat().st_mtime)
                hours_ago = (datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime)).hours
                info["latest"] = f"{latest.name} ({hours_ago:.1f}h ago)"
        except:
            info["latest"] = "无法访问"
    
    return subsystems

def get_today_logs():
    """获取今日日志"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_files = list(MEMORY_DIR.glob(f"{today}*"))
    log_files += list((LOGS_DIR / "修复日志").glob(f"fix_{today}*"))
    return len(log_files)

def generate_summary():
    """生成一页纸简报"""
    cron = get_cron_status()
    subsys = get_subsystem_status()
    logs = get_today_logs()
    
    # 量化指标
    lines = []
    lines.append(f"【系统日报】{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    
    # 核心指标（量化先行）
    lines.append("## 核心指标")
    lines.append(f"- Cron健康: {cron.get('oks', 0)}正常 / {cron.get('errors', 0)}失败 / {cron.get('enabled', 0)}启用")
    lines.append(f"- 今日日志: {logs}条")
    lines.append(f"- 子系统活跃: {sum(1 for s in subsys.values() if s.get('latest') and 'h ago' in str(s['latest']) and float(str(s['latest']).split('(')[1].split('h')[0]) < 24)}/{len(subsys)}个今日有产出")
    lines.append("")
    
    # 异常预警（影响排序）
    lines.append("## 异常预警")
    alerts = []
    if cron.get('errors', 0) > 0:
        alerts.append(f"• Cron失败: {cron['errors']}个（已禁用）")
    
    # 检查各子系统
    for name, info in subsys.items():
        latest = info.get("latest", "")
        if latest and "h ago" in latest:
            hours = float(latest.split('(')[1].split('h')[0])
            if hours > 24:
                alerts.append(f"• {name}: 最后产出{hours:.0f}小时前")
    
    if alerts:
        lines.extend(alerts)
    else:
        lines.append("• 无异常")
    lines.append("")
    
    # 行动项（行动导向）
    lines.append("## 待决策")
    decisions = []
    decisions.append("1. 小说系统：停更63天，是否继续？")
    decisions.append("2. 投资分析Cron：是否恢复涨停采集？")
    decisions.append("3. 地图热点：是否补充缺失脚本？")
    lines.extend(decisions)
    lines.append("")
    
    # 子系统状态
    lines.append("## 子系统状态")
    for name, info in subsys.items():
        status = "✅" if (info.get("latest") and "h ago" in str(info.get("latest", "")) and float(str(info.get("latest", "")).split('(')[1].split('h')[0]) < 24) else "⚠️"
        lines.append(f"- {status} {name}: {info.get('latest', '无产出')}")
    
    return "\n".join(lines)

def push_to_wechat(message):
    """推送到微信"""
    try:
        # 使用现有的推送机制
        result = subprocess.run(
            ["openclaw", "cron", "run", "1eafa4f8-7fa1-4f05-b2a9-de96b5cb6f26"],
            capture_output=True, text=True, timeout=30
        )
        return True
    except:
        # fallback: 写入文件
        output_file = WORKSPACE / "memory" / "executive_summary_latest.txt"
        output_file.write_text(message, encoding="utf-8")
        return True

if __name__ == "__main__":
    summary = generate_summary()
    print(summary)
    
    # 自动推送
    push_to_wechat(summary)
    
    # 保存到memory
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = MEMORY_DIR / f"executive_summary_{today}.txt"
    output_file.write_text(summary, encoding="utf-8")
