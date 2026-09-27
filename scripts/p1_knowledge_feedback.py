#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1 - 知识驱动决策：闭环反馈机制
扫描知识库中的"策略信号"笔记，提取可影响 Cron 行为的信息。
当前规则：
- 投资策略笔记中如果包含 "FAIL" / "回测失败" / "暂缓" → 标记为高风险策略
- 系统优化建议笔记中如果包含 "建议关闭" / "建议暂停" → 自动建议暂停对应 Cron
- 生成报告供 Cron 决策参考
"""

import os
import re
import json
import sys
import datetime
import io

OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"
OUTPUT_DIR = r"C:\Users\Administrator\.openclaw\workspace\out_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 策略信号关键词
STRATEGY_SIGNALS = {
    "high_risk": ["FAIL", "回测失败", "暂缓", "不建议", "风险过高", "止损"],
    "medium_risk": ["注意", "谨慎", "观察", "波动大", "不确定性"],
    "suggestion_pause": ["建议关闭", "建议暂停", "建议停用", "废弃"],
    "suggestion_adjust": ["建议调整", "建议优化", "建议修改", "建议更新"],
}


def scan_knowledge_signals():
    """扫描知识库中所有笔记，提取策略信号"""
    signals = []
    now = datetime.datetime.now().isoformat()

    for root, dirs, files in os.walk(OBSIDIAN_VAULT):
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, OBSIDIAN_VAULT)
            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except:
                continue

            # 跳过日记和索引文件
            if rel.startswith("00-日记") or "索引" in f or "Dataview" in f:
                continue

            for signal_type, keywords in STRATEGY_SIGNALS.items():
                for kw in keywords:
                    for idx, line in enumerate(content.split("\n")):
                        if kw in line and len(line.strip()) < 200:
                            signals.append({
                                "file": rel,
                                "signal_type": signal_type,
                                "keyword": kw,
                                "line": line.strip(),
                                "line_num": idx + 1,
                                "timestamp": now,
                            })
                            break  # 每文件每关键词只取一次

    return signals


def generate_feedback_report(signals):
    """生成闭环反馈报告"""
    high_risk = [s for s in signals if s["signal_type"] == "high_risk"]
    medium_risk = [s for s in signals if s["signal_type"] == "medium_risk"]
    pause_suggestions = [s for s in signals if s["signal_type"] == "suggestion_pause"]
    adjust_suggestions = [s for s in signals if s["signal_type"] == "suggestion_adjust"]

    report = []
    report.append("# P1 知识驱动决策报告")
    report.append(f"生成时间: {datetime.datetime.now().isoformat()}")
    report.append("")
    report.append("---")
    report.append("")

    if high_risk:
        report.append("## 高风险信号")
        report.append("以下笔记包含高风险关键词，建议重点关注：")
        for s in high_risk:
            report.append(f"- [{s['file']}] 第{s['line_num']}行: {s['line']}")
        report.append("")

    if pause_suggestions:
        report.append("## 暂停建议")
        report.append("以下笔记建议暂停某功能：")
        for s in pause_suggestions:
            report.append(f"- [{s['file']}] 第{s['line_num']}行: {s['line']}")
        report.append("")

    if adjust_suggestions:
        report.append("## 调整建议")
        for s in adjust_suggestions:
            report.append(f"- [{s['file']}] 第{s['line_num']}行: {s['line']}")
        report.append("")

    if medium_risk:
        report.append("## 中等风险信号")
        report.append("以下笔记包含中等风险关键词，可关注：")
        for s in medium_risk[:10]:
            report.append(f"- [{s['file']}] 第{s['line_num']}行: {s['line']}")
        report.append("")

    if not signals:
        report.append("## 无信号")
        report.append("当前知识库中未检测到策略调整信号，系统可正常运行。")
        report.append("")

    report.append("---")
    report.append("_由 P1 知识驱动决策系统自动生成_")

    content = "\n".join(report)
    report_path = os.path.join(OUTPUT_DIR, "p1_feedback_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    return report_path, signals


def get_pause_suggestions():
    """对外接口：返回建议暂停的 Cron 任务名"""
    signals = scan_knowledge_signals()
    pause = [s for s in signals if s["signal_type"] == "suggestion_pause"]
    # 尝试从文件名或行内容中提取任务名
    suggestions = []
    for s in pause:
        line = s["line"]
        # 常见模式："建议暂停 XXX"
        m = re.search(r"建议暂停[：: ]*(\S+)", line)
        if m:
            suggestions.append(m.group(1))
    return suggestions


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    signals = scan_knowledge_signals()
    report_path, _ = generate_feedback_report(signals)

    print(f"P1: 扫描完成，共发现 {len(signals)} 个策略信号")
    print(f"P1: 报告已生成: {report_path}")

    if len(sys.argv) > 1 and sys.argv[1] == "--pause":
        suggestions = get_pause_suggestions()
        if suggestions:
            print(f"P1: 建议暂停的Cron任务: {suggestions}")
        else:
            print("P1: 无建议暂停的任务")