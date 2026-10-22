#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
output_monitor.py - 产出监控脚本

功能：
1. 检查各子系统产出目录
2. 统计近7天产出数量
3. 生成监控报告
"""
import os
import json
import datetime
from pathlib import Path

BASE = r"C:\Users\Administrator\.openclaw"
OUTPUTS = {
    "小说章节": os.path.join(BASE, "workspace-novel", "chapters"),
    "自媒体视频": os.path.join(BASE, "workspace-social", "output"),
    "数学动画": os.path.join(BASE, "workspace-math", "output"),
    "地图热点": os.path.join(BASE, "workspace-maphot", "output"),
}

def check_output():
    week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).timestamp()
    results = {}
    for name, path in OUTPUTS.items():
        if not os.path.exists(path):
            results[name] = {"status": "MISSING", "total": 0, "recent": 0}
            continue
        total = 0
        recent = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                if f.startswith("."):
                    continue
                fp = os.path.join(root, f)
                total += 1
                try:
                    if os.path.getmtime(fp) > week_ago:
                        recent += 1
                except:
                    pass
        results[name] = {"status": "OK" if recent > 0 else "STALE", "total": total, "recent": recent}
    return results

def main():
    results = check_output()
    print("=== 产出监控报告 " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + " ===")
    for name, data in results.items():
        print(name + ": " + data["status"] + " (总:" + str(data["total"]) + ", 近7天:" + str(data["recent"]) + ")")
    # 保存报告
    report_path = os.path.join(BASE, "workspace", "memory", "日志", "output_monitor_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("报告已保存: " + report_path)

if __name__ == "__main__":
    main()
