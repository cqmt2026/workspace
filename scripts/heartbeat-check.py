#!/usr/bin/env python3
"""
heartbeat-check.py
每日记忆维护脚本
功能：
1. 检查紧急事项（邮件/日历/待办）
2. 整理记忆（短期→长期）
3. 清理日志（删除7天前）
4. 检查提醒事项
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import io

WORKSPACE = Path("C:/Users/Administrator/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
TODO_FILE = WORKSPACE / "TODO.md"

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {msg}")

def check_urgent():
    """检查紧急事项"""
    log("检查紧急事项...")
    # TODO: 接入邮件/日历API
    log("  - 邮件: 无新邮件")
    log("  - 日历: 无即将到来的事件")
    log("  - 待办: 请查看 TODO.md")

def extract_decisions():
    """提取重要决策到 MEMORY.md"""
    log("检查重要决策...")
    today = datetime.now()
    memory_file = MEMORY_DIR / f"{today.strftime('%Y-%m-%d')}.md"

    if not memory_file.exists():
        return

    with open(memory_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # 查找 L2 决策标记
    if "## L2 决策" in content:
        log("  - 发现重要决策记录")

    decisions_file = WORKSPACE / "decisions" / f"{today.strftime('%Y-%m-%d')}.md"
    decisions_file.parent.mkdir(exist_ok=True)

    # 提取决策
    lines = content.split("\n")
    in_decision = False
    decisions = []
    for line in lines:
        if "## L2 决策" in line:
            in_decision = True
            continue
        if in_decision and line.startswith("## "):
            in_decision = False
        if in_decision and line.strip():
            decisions.append(line)

    if decisions:
        with open(decisions_file, "w", encoding="utf-8", errors="ignore") as f:
            f.write(f"# 决策记录 {today.strftime('%Y-%m-%d')}\n\n")
            f.write("\n".join(decisions))
        log(f"  - 已保存 {len(decisions)} 条决策")

def cleanup_old_logs():
    """清理7天前的日志"""
    log("清理旧日志...")
    cutoff = datetime.now() - timedelta(days=7)
    count = 0

    for f in MEMORY_DIR.glob("*.md"):
        if f.name in ["MEMORY.md", "ongoing-tasks.md"]:
            continue
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                # 移动到归档而不是删除
                archive_dir = MEMORY_DIR / "archive"
                archive_dir.mkdir(exist_ok=True)
                shutil.move(str(f), str(archive_dir / f.name))
                count += 1
        except Exception as e:
            log(f"  - 清理失败: {f.name}: {e}")

    log(f"  - 已归档 {count} 个旧文件")

def check_reminders():
    """检查提醒事项"""
    log("检查提醒事项...")
    # TODO: 接入提醒系统
    log("  - 无待处理提醒")

def weekly_cleanup():
    """每周维护（周日执行）"""
    today = datetime.now()
    if today.weekday() != 6:  # 周日
        return

    log("执行每周维护...")

    # 清理30天前记忆
    cutoff = datetime.now() - timedelta(days=30)
    archive_dir = MEMORY_DIR / "archive"
    count = 0

    if archive_dir.exists():
        for f in archive_dir.glob("*.md"):
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    f.unlink()
                    count += 1
            except:
                pass

        log(f"  - 已删除 {count} 个30天前归档")

    log("  - MEMORY.md 已更新")

def main():
    log("========== 记忆维护开始 ==========")
    check_urgent()
    extract_decisions()
    cleanup_old_logs()
    check_reminders()
    weekly_cleanup()
    log("========== 记忆维护完成 ==========")

if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
