#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
restore_cron.py - 恢复Cron自动化任务配置

功能：
1. 从cron_dump2.json读取历史任务配置
2. 恢复到openclaw.json的automations字段
3. 重置失败计数

用法：
    python restore_cron.py [--dry-run]
"""

import os
import sys
import json
import argparse
from datetime import datetime

# 路径配置
BASE = r"C:\Users\Administrator\.openclaw"
CONFIG_PATH = os.path.join(BASE, "openclaw.json")
BACKUP_PATH = CONFIG_PATH + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
DUMP_PATH = os.path.join(BASE, "workspace", "scripts", "cron_dump2.json")

def load_dump():
    """加载历史任务配置"""
    if not os.path.exists(DUMP_PATH):
        print("错误: 找不到历史配置 " + DUMP_PATH)
        return None
    
    with open(DUMP_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    jobs = data.get("jobs", [])
    print("从历史记录加载 " + str(len(jobs)) + " 个任务")
    return jobs

def load_current_config():
    """加载当前配置"""
    if not os.path.exists(CONFIG_PATH):
        print("错误: 找不到配置文件 " + CONFIG_PATH)
        return None
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(data):
    """保存配置"""
    # 备份
    import shutil
    shutil.copy(CONFIG_PATH, BACKUP_PATH)
    print("备份已创建: " + BACKUP_PATH)
    
    # 保存
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("配置已更新")

def restore_cron(dry_run=False):
    """恢复Cron配置"""
    # 加载历史任务
    jobs = load_dump()
    if jobs is None:
        return False
    
    # 加载当前配置
    config = load_current_config()
    if config is None:
        return False
    
    # 构建automations字典
    automations = {}
    for job in jobs:
        name = job.get("name", "")
        if not name:
            continue
        
        # 构建自动化配置
        auto_config = {
            "enabled": job.get("enabled", True),
            "schedule": job.get("schedule", ""),
            "command": job.get("command", ""),
            "timeoutSeconds": job.get("timeoutSeconds", 120),
            "failCount": 0,  # 重置失败计数
            "lastRunAt": None,
            "nextRunAt": None,
        }
        
        # 复制可选字段
        for key in ["description", "stdin", "workingDirectory"]:
            if key in job:
                auto_config[key] = job[key]
        
        automations[name] = auto_config
    
    print("准备恢复 " + str(len(automations)) + " 个任务")
    
    if dry_run:
        print()
        print("=== 待恢复任务列表 ===")
        for name, auto in automations.items():
            status = "ENABLED" if auto["enabled"] else "DISABLED"
            print(status + ": " + name + " (" + auto["schedule"] + ")")
        return True
    
    # 更新配置
    config["automations"] = automations
    save_config(config)
    
    print()
    print("=== 恢复完成 ===")
    print("已恢复 " + str(len(automations)) + " 个自动化任务")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="恢复Cron自动化任务配置")
    parser.add_argument("--dry-run", action="store_true", help="仅显示不执行")
    args = parser.parse_args()
    
    success = restore_cron(dry_run=args.dry_run)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
