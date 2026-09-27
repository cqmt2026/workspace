# -*- coding: utf-8 -*-
"""
sync_core_docs.py - 自动同步核心文档
当检测到系统状态变化时，自动更新相关文档
"""

import os
import sys
import json
import subprocess
from datetime import datetime
import io

WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"

def get_gateway_version():
    """获取当前Gateway版本"""
    try:
        result = subprocess.run(
            ["openclaw", "--version"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if "OpenClaw" in line:
                return line.strip()
        return None
    except Exception as e:
        print("[sync_core_docs] error: %s" % e)
        return None

def get_cron_jobs():
    """获取当前cron任务列表"""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=15
        )
        data = json.loads(result.stdout)
        jobs = []
        for j in data.get("jobs", []):
            jobs.append({
                "name": j.get("name", ""),
                "enabled": j.get("enabled", False),
                "schedule": j.get("schedule", {})
            })
        return jobs
    except Exception as e:
        print("[sync_core_docs] error: %s" % e)
        return []

def update_agents_md():
    """更新AGENTS.md - 版本和子系统路径"""
    changes = []
    filepath = os.path.join(WORKSPACE, "AGENTS.md")
    
    # 获取gateway版本
    version = get_gateway_version()
    if version:
        version_str = version.replace("OpenClaw ", "").strip()
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查版本是否需要更新
        old_version = None
        for line in content.split("\n"):
            if "版本" in line and "20" in line:
                old_version = line.strip()
        
        if old_version and version_str not in content:
            # 版本已更新
            new_content = content.replace(old_version, f"- **版本**: {version_str} ✅")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            changes.append(f"AGENTS.md: 版本更新")
    
    # 检查子系统目录是否存在
    subsystems = {
        "workspace-novel": r"workspace\workspace-novel",
        "workspace-investment": r"workspace\workspace-investment",
        "workspace-social": r"workspace\workspace-social",
        "workspace-jianying": r"workspace\workspace-jianying",
        "workspace-math": r"workspace\workspace-math"
    }
    
    for sub_name, sub_path in subsystems.items():
        full_path = os.path.join(WORKSPACE, sub_path)
        exists = os.path.exists(full_path)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否在文档中（支持多种格式：加粗、代码块、普通文本）
        # 先尝试加粗格式
        marker_bold = f"**{sub_name}**"
        marker_plain = sub_name  # 普通文本匹配
        if exists and marker_bold not in content and marker_plain not in content:
            # 需要添加新子系统
            changes.append(f"AGENTS.md: 发现新子系统 {sub_name}")
    
    return changes

def update_tools_md():
    """更新TOOLS.md - cron任务列表"""
    filepath = os.path.join(WORKSPACE, "TOOLS.md")
    jobs = get_cron_jobs()
    
    if not jobs:
        return []
    
    changes = []
    cron_lines = []
    for job in jobs:
        name = job["name"]
        enabled = "✅" if job["enabled"] else "❌"
        cron_lines.append(f"| {name} | {enabled} |")
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 简单检查：如果cron任务数量变化了（从10个变化）
    current_count = content.count("✅") + content.count("❌")
    if len(jobs) != current_count and len(jobs) > 0:
        changes.append(f"TOOLS.md: Cron任务数量变化({current_count}->{len(jobs)})")
    
    return changes

def update_session_state():
    """更新proactivity/session-state.md - 保持当前状态"""
    # 这个文件通常由主Agent主动维护
    # 只是检查是否存在
    path = os.path.join(WORKSPACE, "proactivity", "session-state.md")
    if not os.path.exists(path):
        return ["session-state.md: 文件缺失，需要创建"]
    return []

def main():
    changes = []
    
    changes.extend(update_agents_md())
    changes.extend(update_tools_md())
    changes.extend(update_session_state())
    
    if changes:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 发现{len(changes)}处更新:")
        for c in changes:
            print(f"  - {c}")
        # 追加到同步日志
        log_file = os.path.join(WORKSPACE, "memory", "文档", "core_sync_log.md")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            for c in changes:
                f.write(f"- {c}\n")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 无需更新")
    
    return changes

if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()