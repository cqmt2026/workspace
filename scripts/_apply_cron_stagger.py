# -*- coding: utf-8 -*-
"""
应用 Cron 错峰调度配置
修改13个任务的schedule，避免并发触发rate limit
"""
import json
import subprocess
import sys

# 错峰调度配置
stagger_config = [
    {"jobId": "2efc38a0-8613-42d7-82cd-2951429ebdd0", "name": "AI-Retry-错题AI重试", "newExpr": "30 9,15 * * *"},
    {"jobId": "e53ad37d-bc37-42dc-87cc-e91fa5ed1d30", "name": "INV-Daily-Analysis", "newExpr": "45 16 * * *"},
    {"jobId": "1eafa4f8-7fa1-4f05-b2a9-de96b5cb6f26", "name": "Daily-Evening-Report-晚间汇报", "newExpr": "30 18 * * *"},
    {"jobId": "dd6452dc-4f85-49cb-a60f-d1d9004c3679", "name": "Memory-Recall-启动上下文召回", "newExpr": "20 9,18 * * *"},
    {"jobId": "afb40d90-9551-4f2a-b9da-44034ba5156d", "name": "Self-Learning-统一学习", "newExpr": "30 21 * * *"},
    {"jobId": "21a9f8de-cde7-4207-a017-40d7ef33ef85", "name": "LOG-日志审计-晚间检查", "newExpr": "30 22 * * *"},
    {"jobId": "f46fa77a-6255-4457-a97b-cc3d29e43e24", "name": "INV-MXSearch-采集-22:00", "newExpr": "45 22 * * *"},
    {"jobId": "ee6739ce-5cf6-47bb-8a38-830ecaa74b1f", "name": "Daily-Inspection-每日巡检", "newExpr": "25 9 * * *"},
    {"jobId": "f3475161-b643-4a0a-a950-ea9a574e673c", "name": "Daily-Morning-Report-早间汇报", "newExpr": "35 9 * * *"},
    {"jobId": "22d19601-cae9-4bd7-bac2-3dd9aba3c28e", "name": "LOG-日志审计-每日检查", "newExpr": "40 9 * * *"},
    {"jobId": "f48c5e9c-95fd-4ef8-b542-6f8dd1c34dd4", "name": "P3-时效管理", "newExpr": "50 22 * * *"},
    {"jobId": "84ea7317-aae6-4bbb-830b-df72b88068a1", "name": "P0-读取率监控", "newExpr": "35 22 * * *"},
    {"jobId": "0b0c2ffd-157f-40de-b5ce-76a7091a61a0", "name": "P1-知识驱动决策", "newExpr": "40 22 * * *"},
]

print("=== 应用 Cron 错峰调度配置 ===\n")

results = []
for job in stagger_config:
    job_id = job["jobId"]
    name = job["name"]
    new_expr = job["newExpr"]

    print(f"处理: {name}")
    print(f"  Job ID: {job_id}")
    print(f"  新调度: {new_expr}")

    # 尝试通过automations API更新
    # 由于权限限制，这里只记录配置，不实际执行
    results.append({
        "jobId": job_id,
        "name": name,
        "newSchedule": new_expr,
        "status": "pending_manual"
    })
    print(f"  状态: 待手动应用\n")

# 生成应用脚本
output_file = r"C:\Users\Administrator\.openclaw\workspace\memory\日志\system_check\apply_cron_stagger_commands.bat"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("@echo off\n")
    f.write("chcp 65001 >nul\n")
    f.write("echo === 应用 Cron 错峰调度配置 ===\n\n")
    for r in results:
        f.write(f'echo 处理: {r["name"]}\n')
        f.write(f'openclaw cron update {r["jobId"]} --schedule "{r["newSchedule"]}"\n\n')
    f.write("echo === 完成 ===\n")

print(f"=== 生成应用脚本 ===")
print(f"脚本路径: {output_file}")
print(f"\n请手动运行此脚本应用配置，或使用以下命令逐个更新:")
print()
for r in results:
    print(f'  openclaw cron update {r["jobId"]} --schedule "{r["newSchedule"]}"')
