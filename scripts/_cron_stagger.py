# -*- coding: utf-8 -*-
"""
Cron 错峰调度脚本
将高失败率任务分散到不同时区，避免并发触发rate limit
"""
import json
from datetime import datetime

# 当前失败任务及其建议调度时间
jobs_to_adjust = [
    # (job_id, current_expr, suggested_expr, reason)
    ("2efc38a0-8613-42d7-82cd-2951429ebdd0", "12 9,15 * * *", "30 9,15 * * *", "AI-Retry: 从:12延后到:30"),
    ("e53ad37d-bc37-42dc-87cc-e91fa5ed1d30", "15 16 * * *", "45 16 * * *", "INV-Daily-Analysis: 从:15延后到:45"),
    ("1eafa4f8-7fa1-4f05-b2a9-de96b5cb6f26", "0 18 * * *", "30 18 * * *", "Daily-Evening-Report: 从:00延后到:30"),
    ("dd6452dc-4f85-49cb-a60f-d1d9004c3679", "0 9,18 * * *", "20 9,18 * * *", "Memory-Recall: 从:00延后到:20"),
    ("afb40d90-9551-4f2a-b9da-44034ba5156d", "0 21 * * *", "30 21 * * *", "Self-Learning: 从:00延后到:30"),
    # 其他失败任务
    ("21a9f8de-cde7-4207-a017-40d7ef33ef85", "0 22 * * *", "30 22 * * *", "LOG-日志审计-晚间"),
    ("f46fa77a-6255-4457-a97b-cc3d29e43e24", "0 22 * * *", "45 22 * * *", "INV-MXSearch-采集"),
    ("ee6739ce-5cf6-47bb-8a38-830ecaa74b1f", "0 9 * * *", "25 9 * * *", "Daily-Inspection"),
    ("f3475161-b643-4a0a-a950-ea9a574e673c", "0 9 * * *", "35 9 * * *", "Daily-Morning-Report"),
    ("22d19601-cae9-4bd7-bac2-3dd9aba3c28e", "0 9 * * *", "40 9 * * *", "LOG-日志审计-每日检查"),
    ("f48c5e9c-95fd-4ef8-b542-6f8dd1c34dd4", "45 22 * * *", "50 22 * * *", "P3-时效管理"),
    ("84ea7317-aae6-4bbb-830b-df72b88068a1", "30 22 * * *", "35 22 * * *", "P0-读取率监控"),
    ("0b0c2ffd-157f-40de-b5ce-76a7091a61a0", "35 22 * * *", "40 22 * * *", "P1-知识驱动决策"),
]

print("=== Cron 错峰调度方案 ===")
print(f"共需调整 {len(jobs_to_adjust)} 个任务\n")

# 按时间段分组
morning = [j for j in jobs_to_adjust if '9 *' in j[2] or '09' in j[2]]
afternoon = [j for j in jobs_to_adjust if '16 *' in j[2] or '18 *' in j[2] or '15 *' in j[2]]
evening = [j for j in jobs_to_adjust if '21 *' in j[2] or '22 *' in j[2] or '18 *' in j[2]]

print("早间区（09:00-09:45）:")
for j in morning:
    print(f"  {j[3]}: {j[1]} → {j[2]}")

print("\n午间区（15:00-16:45）:")
for j in afternoon:
    print(f"  {j[3]}: {j[1]} → {j[2]}")

print("\n晚间区（18:00-22:50）:")
for j in evening:
    print(f"  {j[3]}: {j[1]} → {j[2]}")

print("\n=== 调度原则 ===")
print("1. 同一时间段内任务间隔≥10分钟")
print("2. 高LLM消耗任务（Analysis/Learning）放在时段末尾")
print("3. 轻量任务（Logs/Audit）放在时段开头")
print("4. 避免0分/30分整点集中触发")

# 生成JSON配置（供手动应用）
config = []
for j in jobs_to_adjust:
    config.append({
        "jobId": j[0],
        "name": j[3].split(": ")[0],
        "currentSchedule": j[1],
        "suggestedSchedule": j[2],
        "reason": j[3]
    })

output_file = r"C:\Users\Administrator\.openclaw\workspace\memory\日志\system_check\cron_stagger_config_20260905.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"\n配置已保存到: {output_file}")
