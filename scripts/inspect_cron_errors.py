#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""inspect_cron_errors.py - 检查Cron错误任务的command配置"""
import subprocess, json, os

BASE = r"C:\Users\Administrator\.openclaw"
CLI = r"C:\Users\Administrator\AppData\Roaming\npm\openclaw.cmd"

ERROR_NAMES = [
    "core-fix-check",
    "core-experience-learning", 
    "core-tool-validation",
    "core-task-inference",
    "core-review",
    "daily-backup"
]

def get_jobs():
    try:
        r = subprocess.run(f'"{CLI}" gateway call cron.list', shell=True,
                          capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
        if r.returncode != 0:
            return []
        idx = r.stdout.find('{')
        if idx < 0:
            return []
        data = json.loads(r.stdout[idx:])
        return data.get('jobs', [])
    except:
        return []

def main():
    jobs = get_jobs()
    print(f"总计 {len(jobs)} 个任务\n")
    
    for name in ERROR_NAMES:
        matched = [j for j in jobs if j['name'] == name]
        if matched:
            j = matched[0]
            print(f"\n{'='*50}")
            print(f"任务: {j['name']}")
            print(f"ID: {j.get('id', '')}")
            print(f"agentId: {j.get('agentId', '')}")
            print(f"错误: {j.get('lastRunError', 'N/A')[:100]}")
            print(f"command: {j.get('command', 'N/A')}")
            print(f"schedule: {j.get('schedule', {})}")
        else:
            print(f"\n未找到: {name}")

if __name__ == '__main__':
    main()
