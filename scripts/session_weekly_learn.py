#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_weekly_learn.py - 每周Session学习总结
读取一周的Session分析报告 → 提取重要模式/趋势 → 存入Obsidian知识库

用法:
    python session_weekly_learn.py               # 分析本周
    python session_weekly_learn.py --week 2026-W28  # 指定周
"""

import os
import sys
import json
import glob
import re
import datetime
from collections import Counter, defaultdict
import io

sys.stdout.reconfigure(encoding='utf-8')

OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"
REPORT_DIR = r"F:\Obsidian\Jarvis\03-项目\贾维斯系统"
STATE_FILE = os.path.join(os.path.dirname(__file__), ".session_weekly_state.json")


def get_week_range(week_str=None):
    """获取指定周的起止日期"""
    today = datetime.date.today()
    if week_str:
        year, week = int(week_str[:4]), int(week_str[-2:])
        # ISO周
        d = datetime.date.fromisocalendar(year, week, 1)
    else:
        d = today - datetime.timedelta(days=today.weekday())
    start = d
    end = d + datetime.timedelta(days=6)
    return start.isoformat(), end.isoformat()


def scan_report_files(start_date, end_date):
    """扫描Obsidian中的Session分析报告"""
    report_dir = os.path.join(OBSIDIAN_VAULT, "03-项目", "贾维斯系统")
    if not os.path.exists(report_dir):
        return []

    reports = []
    for f in sorted(glob.glob(os.path.join(report_dir, "*.md"))):
        fname = os.path.basename(f)
        # 匹配文件名中的日期
        m = re.search(r'Session分析报告_(\d{4}-\d{2}-\d{2})', fname)
        if m:
            report_date = m.group(1)
            if start_date <= report_date <= end_date:
                with open(f, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                reports.append({"date": report_date, "content": content, "path": f})
    return reports


def extract_metrics(report_content):
    """从报告文本中提取关键指标"""
    metrics = {}
    
    # 总Session数
    m = re.search(r'\|\s*Session总数\s*\|\s*(\d+)\s*\|', report_content)
    if m: metrics["total"] = int(m.group(1))
    
    # 对话Session
    m = re.search(r'\|\s*对话Session\s*\|\s*(\d+)\s*\|', report_content)
    if m: metrics["dialog"] = int(m.group(1))
    
    # CronSession
    m = re.search(r'\|\s*Cron任务Session\s*\|\s*(\d+)\s*\|', report_content)
    if m: metrics["cron"] = int(m.group(1))
    
    # 异常Session
    m = re.search(r'\|\s*异常Session\s*\|\s*(\d+)\s*\|', report_content)
    if m: metrics["errors"] = int(m.group(1))
    
    # Token消耗
    m = re.search(r'\|\s*总Token消耗\s*\|\s*([\d,]+)\s*\|', report_content)
    if m: metrics["tokens"] = int(m.group(1).replace(",", ""))
    
    # 健康度
    m = re.search(r'\*\*(✅ 健康|⚠️ 轻微异常|🔴 需要关注)\*\*', report_content)
    if m: metrics["health"] = m.group(1)
    
    # 异常任务列表
    errors = []
    for m in re.finditer(r'-\s*\*\*(.*?)\*\*.*?:\s*(.*?)(?:\n|$)', report_content):
        errors.append(f"{m.group(1)}: {m.group(2)[:80]}")
    metrics["error_details"] = errors
    
    # Cron任务执行表
    cron_tasks = {}
    for m in re.finditer(r'\|\s*(\S[\w/]+)\s*\|\s*(\d+)\s*\|\s*(✅|⚠️\d*|🔴)\s*\|\s*([\d,]+)\s*\|', report_content):
        name = m.group(1).strip()
        count = int(m.group(2))
        status = m.group(3).strip()
        tokens = int(m.group(4).replace(",", ""))
        cron_tasks[name] = {"count": count, "status": status, "tokens": tokens}
    metrics["cron_tasks"] = cron_tasks
    
    return metrics


def analyze_weekly_patterns(metrics_list):
    """分析一周的模式"""
    analysis = {
        "total_sessions": sum(m.get("total", 0) for m in metrics_list),
        "total_dialog": sum(m.get("dialog", 0) for m in metrics_list),
        "total_cron": sum(m.get("cron", 0) for m in metrics_list),
        "total_errors": sum(m.get("errors", 0) for m in metrics_list),
        "total_tokens": sum(m.get("tokens", 0) for m in metrics_list),
        "avg_daily_tokens": 0,
        "error_days": 0,
        "healthy_days": 0,
        "recurring_errors": [],
        "top_cron_tasks": [],
        "dialog_days": 0,
    }

    for m in metrics_list:
        if m.get("errors", 0) > 0:
            analysis["error_days"] += 1
        else:
            analysis["healthy_days"] += 1
        if m.get("dialog", 0) > 0:
            analysis["dialog_days"] += 1

    days = len(metrics_list)
    if days > 0:
        analysis["avg_daily_tokens"] = analysis["total_tokens"] // days

    # 统计重复出现的错误
    error_counter = Counter()
    for m in metrics_list:
        for err in m.get("error_details", []):
            error_counter[err] += 1
    analysis["recurring_errors"] = [(e, c) for e, c in error_counter.most_common(10) if c > 1]

    # 统计Cron任务执行频次
    cron_counter = Counter()
    for m in metrics_list:
        for task_name in m.get("cron_tasks", {}):
            cron_counter[task_name] += 1
    analysis["top_cron_tasks"] = cron_counter.most_common(20)

    return analysis


def build_weekly_report(analysis, start_date, end_date):
    """生成周报"""
    report = []
    report.append(f"# 📊 周Session分析报告 — {start_date} ~ {end_date}")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## 一、周度概览")
    report.append("")
    report.append(f"| 指标 | 数值 |")
    report.append(f"|------|------|")
    report.append(f"| 覆盖天数 | 7天 |")
    report.append(f"| 总Session | {analysis['total_sessions']:,} |")
    report.append(f"| 对话Session | {analysis['total_dialog']:,} |")
    report.append(f"| Cron任务Session | {analysis['total_cron']:,} |")
    report.append(f"| 总Token消耗 | {analysis['total_tokens']:,} |")
    report.append(f"| 日均Token消耗 | {analysis['avg_daily_tokens']:,} |")
    report.append(f"| 健康天数 | {analysis['healthy_days']}/7 |")
    report.append(f"| 有异常天数 | {analysis['error_days']}/7 |")
    report.append(f"| 有对话天数 | {analysis['dialog_days']}/7 |")
    report.append("")

    # 重复错误分析
    if analysis["recurring_errors"]:
        report.append("## ⚠️ 重复异常")
        report.append("")
        report.append("以下异常在本周多次出现，建议关注：")
        report.append("")
        for err, count in analysis["recurring_errors"]:
            report.append(f"- [{count}次] {err[:120]}")
        report.append("")

    # Cron任务执行模式
    report.append("## 二、Cron任务执行模式")
    report.append("")
    report.append("| 任务 | 执行天数/7 | 日均Token |")
    report.append("|------|-----------|----------|")
    for task, days in analysis["top_cron_tasks"]:
        report.append(f"| {task} | {days}/7 | - |")
    report.append("")

    # 对话活跃度
    report.append("## 三、对话活跃度")
    report.append("")
    if analysis["dialog_days"] == 0:
        report.append("本周无主人对话记录。")
    else:
        report.append(f"本周有 {analysis['dialog_days']} 天有对话记录，共 {analysis['total_dialog']} 个对话Session。")
    report.append("")

    # 趋势判断
    report.append("## 四、趋势判断")
    report.append("")
    error_rate = analysis["total_errors"] / max(analysis["total_sessions"], 1) * 100
    if error_rate > 10:
        report.append(f"- ❌ 异常率 {error_rate:.1f}%，偏高，需要排查")
    elif error_rate > 5:
        report.append(f"- ⚠️ 异常率 {error_rate:.1f}%，略高，建议关注")
    else:
        report.append(f"- ✅ 异常率 {error_rate:.1f}%，正常")

    token_trend = ""
    if analysis["avg_daily_tokens"] > 50000:
        token_trend = "Token消耗较高，建议关注成本"
    elif analysis["avg_daily_tokens"] > 20000:
        token_trend = "Token消耗适中"
    else:
        token_trend = "Token消耗较低"
    report.append(f"- {token_trend}（日均{analysis['avg_daily_tokens']:,}）")

    if analysis["dialog_days"] < 3:
        report.append("- 主人对话频率较低，系统自动化运行为主")
    else:
        report.append("- 主人有定期对话，系统互动正常")
    report.append("")

    report.append("---")
    report.append(f"_由 可悦🌸 于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} 自动生成_")

    return "\n".join(report)


def save_to_obsidian(title, content, category="系统"):
    sys.path.insert(0, os.path.dirname(__file__))
    from obsidian_save import save_note
    return save_note(title, content, category)


def save_knowledge_note(analysis, start_date, end_date):
    """提取重要知识写入知识库"""
    content = []
    content.append("## Session模式知识\n")
    content.append(f"**周期**: {start_date} ~ {end_date}\n")

    # 异常模式
    if analysis["recurring_errors"]:
        content.append("### 已知异常模式\n")
        for err, count in analysis["recurring_errors"]:
            content.append(f"- [{count}次] {err}")
        content.append("")

    # Cron任务运行情况
    content.append("### 活跃Cron任务\n")
    for task, days in analysis["top_cron_tasks"]:
        content.append(f"- {task}: {days}/7天")
    content.append("")

    # 对话活跃度
    content.append(f"### 对话活跃度\n")
    content.append(f"- 周对话Session: {analysis['total_dialog']}")
    content.append(f"- 有对话天数: {analysis['dialog_days']}/7")
    content.append("")

    content.append("---\n")
    content.append(f"_由 session_weekly_learn.py 自动提取_\n")

    return "".join(content)


def main():
    # 确定周范围
    if len(sys.argv) > 2 and sys.argv[1] == "--week":
        week_str = sys.argv[2]
    else:
        today = datetime.date.today()
        week_str = today.strftime("%Y-W%W")

    start_date, end_date = get_week_range(week_str)

    # 扫描报告文件
    reports = scan_report_files(start_date, end_date)
    if not reports:
        print(f"⚠️ {start_date} ~ {end_date} 没有找到Session分析报告")
        print("请先运行 session_daily_report.py 生成日报")
        return

    print(f"📊 分析 {start_date} ~ {end_date}，共 {len(reports)} 天数据")

    # 提取指标
    metrics_list = []
    for r in reports:
        m = extract_metrics(r["content"])
        if m:
            m["date"] = r["date"]
            metrics_list.append(m)

    if not metrics_list:
        print("⚠️ 无法从报告中提取指标")
        return

    # 分析模式
    analysis = analyze_weekly_patterns(metrics_list)

    # 生成周报
    weekly_report = build_weekly_report(analysis, start_date, end_date)

    # 保存到Obsidian
    try:
        fp = save_to_obsidian(f"周Session分析报告_{start_date}", weekly_report, "系统")
        print(f"✅ 周报已保存: {fp}")
    except Exception as e:
        print(f"⚠️ 保存周报失败: {e}")

    # 提取知识，存入知识库
    try:
        knowledge = save_knowledge_note(analysis, start_date, end_date)
        fp2 = save_to_obsidian(f"Session知识沉淀_{start_date}", knowledge, "系统")
        print(f"✅ 知识沉淀已保存: {fp2}")
    except Exception as e:
        print(f"⚠️ 保存知识沉淀失败: {e}")

    print(f"\n📋 周报摘要: {analysis['total_sessions']}个Session, {analysis['total_errors']}个异常, {analysis['total_tokens']:,} tokens")


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()