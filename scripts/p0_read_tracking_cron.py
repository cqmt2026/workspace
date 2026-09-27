#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0读取率监控 - Cron版本
扫描笔记，更新跟踪，生成报告
"""
import sys
import os
import json
import datetime

WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"
sys.path.insert(0, WORKSPACE)

TRACK_FILE = os.path.join(r"F:\\Obsidian\\Jarvis", ".read_tracking.json")

def main():
    # 直接读取 .read_tracking.json
    if os.path.exists(TRACK_FILE):
        with open(TRACK_FILE, "r", encoding="utf-8") as f:
            tracking = json.load(f)
    else:
        # 如果文件不存在，用原脚本扫描
        from scripts.p0_read_tracking import scan_and_update_read_counts, load_tracking
        tracking = scan_and_update_read_counts()
    
    # 修复字段名："read_count" vs "read_count" vs "readCount"
    for rel, data in tracking.items():
        if "read_count" not in data and "readCount" in data:
            data["read_count"] = data["readCount"]
            del data["readCount"]
        if "last_read_at" not in data and "lastReadAt" in data:
            data["last_read_at"] = data["lastReadAt"]
            del data["lastReadAt"]
    
    # 生成 unread 列表
    now = datetime.datetime.now()
    unread = []
    for rel, data in tracking.items():
        lr = data.get("last_read_at", "")
        if lr:
            try:
                dt = datetime.datetime.fromisoformat(lr)
                if (now - dt).days >= 30:
                    unread.append((rel, data.get("read_count", 0), lr))
            except:
                unread.append((rel, data.get("read_count", 0), lr))
    unread.sort(key=lambda x: x[1])
    
    # 日志目录
    log_dir = os.path.join(WORKSPACE, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "p0_read_tracking.log")
    
    lines = []
    lines.append(f"[{datetime.datetime.now().isoformat()}] P0读取率监控")
    lines.append(f"  共跟踪 {len(tracking)} 篇笔记")
    lines.append(f"  超过30天未读取: {len(unread)} 篇")
    
    if unread:
        lines.append("  未读取列表:")
        for rel, rc, lr in unread[:20]:
            lines.append(f"    {rel} (read_count={rc}, last_read={lr})")
    else:
        lines.append("  所有笔记均有最近读取记录")
    
    # 读取频率前10
    sorted_by_rc = sorted(tracking.items(), key=lambda x: x[1]["read_count"], reverse=True)
    lines.append("  读取频率排名前10:")
    for rel, data in sorted_by_rc[:10]:
        lines.append(f"    {rel}: read_count={data['read_count']}")
    
    # 追加写入日志
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n\n")
    
    # 输出到stdout（cron会捕获）
    print("\n".join(lines))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
