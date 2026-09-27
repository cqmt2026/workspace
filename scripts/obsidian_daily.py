#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可悦 → Obsidian 日记生成
每天自动生成当日日记，使用已有日记模板
"""

import os
import sys
import datetime
import json
import glob
import io

OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"
WORKSPACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# 日记模板路径
TEMPLATE_PATH = os.path.join(OBSIDIAN_VAULT, "00-日记", "日记模板.md")


def get_daily_summary():
    """收集当天的系统活动摘要"""
    today = datetime.date.today().isoformat()
    summary = []
    
    # Cron任务执行情况
    cron_logs = []
    log_dir = os.path.join(WORKSPACE, "logs")
    if os.path.exists(log_dir):
        for f in os.listdir(log_dir):
            if today in f and f.endswith(".log"):
                task_name = f.replace(today, "").replace("_", "").replace(".log", "").strip("-_")
                log_path = os.path.join(log_dir, f)
                mtime = os.path.getmtime(log_path)
                cron_logs.append(f"  - {task_name}")
    
    if cron_logs:
        summary.append("## ⚙️ 今日系统运行")
        summary.append(f"共执行 {len(cron_logs)} 个Cron任务：")
        summary.extend(cron_logs[:15])
        if len(cron_logs) > 15:
            summary.append(f"  ...及其他 {len(cron_logs)-15} 个任务")
        summary.append("")
    
    # 知识沉淀记录
    obs_dir = os.path.join(OBSIDIAN_VAULT, "03-投资")
    if os.path.exists(obs_dir):
        today_notes = 0
        for root, dirs, files in os.walk(obs_dir):
            for f in files:
                if today in f and f.endswith(".md"):
                    today_notes += 1
        if today_notes > 0:
            summary.append(f"## 📝 今日知识沉淀")
            summary.append(f"新增 {today_notes} 篇知识笔记")
            summary.append("")
    
    # 投资系统状态
    ml_result = os.path.join(WORKSPACE, "workspace-investment", "quant_ml", "logs", "quant_ml_v1", "results.json")
    if os.path.exists(ml_result):
        try:
            with open(ml_result, "r", encoding="utf-8") as f:
                data = json.load(f)
            auc = data.get("auc", "?")
            summary.append(f"## 📈 投资系统")
            summary.append(f"ML模型AUC: {auc}")
            summary.append("")
        except:
            pass
    
    return "\n".join(summary)


def generate_daily_note():
    """生成当日日记"""
    today = datetime.date.today()
    filename = f"{today.isoformat()}.md"
    filepath = os.path.join(OBSIDIAN_VAULT, "00-日记", filename)
    
    # 如果已存在则跳过
    if os.path.exists(filepath):
        print(f"日记已存在: {filepath}")
        return filepath
    
    # 生成日记内容
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_names[today.weekday()]
    
    summary = get_daily_summary()
    
    md = f"""# {today.isoformat()} ({weekday})

## 📌 今日要事
- 

## 💡 灵感/想法
- 

## 📝 备忘
- 

## 🌸 可悦学习
{summary}

---
_由 可悦🌸 自动创建_
"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)
    
    print(f"✅ 日记已生成: {filepath}")
    return filepath


def main():
    print(f"🌸 可悦日记生成 - {datetime.datetime.now().isoformat()}")
    generate_daily_note()
    print("🌸 日记生成完成")


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()