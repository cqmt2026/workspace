#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_daily_report.py - 每日Session分析报告
读取当天所有Session文件 → 统计 → 分类 → 产出Markdown报告 → 存入Obsidian

用法:
    python session_daily_report.py               # 分析当天
    python session_daily_report.py --date 2026-07-09  # 指定日期
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

SESSION_DIR = r"C:\Users\Administrator\.openclaw\agents\main\sessions"
OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"
STATE_FILE = os.path.join(os.path.dirname(__file__), ".session_daily_state.json")

# 心跳/系统维护类关键词（不计入"对话"）
SYSTEM_KEYWORDS = [
    "HEARTBEAT_OK", "NO_REPLY", "HEARTBEAT", "System-Maintenance",
    "PREFERENCES", "Auto-Stagger", "Self-Optimize", "综合维护",
    "Session-Backup", "Token-Monitor", "维护完成", "维护完毕",
    "skip", "skipped", "no action",
]

# 已知Cron任务映射（用于识别）
CRON_TASKS = {
    "System-Maintenance": "系统维护",
    "Hot-Topic-Finder": "热点采集",
    "Web-Hot": "全网热点",
    "Daily-Morning-Report": "早报",
    "INV-RPS": "RPS推送",
    "INV-Morning-Brief": "早盘参考",
    "INV-Closing-Strategy": "尾盘策略",
    "INV-Closing-Report": "收盘报告",
    "INV-ZT-Kline": "涨停K线",
    "INV-ML": "ML训练",
    "INV-每日分析": "每日分析",
    "AI-Retry": "错题重试",
    "LOG-审计": "日志审计",
    "Obsidian-日记": "日记生成",
    "Obsidian-知识沉淀": "知识沉淀",
    "Obsidian-会话沉淀": "会话沉淀",
    "Obsidian-知识库审计": "知识库审计",
    "Obsidian-知识关联": "知识关联",
    "Obsidian-领域关系图": "关系图更新",
    "Obsidian-今日推荐": "今日推荐",
    "P0-读取率监控": "读取率监控",
    "P1-知识驱动决策": "知识驱动决策",
    "P2-语义关联": "语义关联",
    "P3-时效管理": "时效管理",
    "Self-Learning": "自我学习",
    "Novel-自我学习": "小说学习",
    "Social-自我学习": "自媒体学习",
    "Math-自动学习": "数学动画学习",
    "WX-知识库更新": "小程序知识库",
    "WX-Corrections": "小程序Corrections",
    "Memory Dreaming": "记忆收编",
    "Core-Docs-Sync": "文档同步",
    "子系统健康检查": "健康检查",
    "Cross-System-Bridge": "跨系统推荐",
    "流程问题检测": "流程检测",
    "周巡检": "周巡检",
    "备份清理": "备份清理",
    "安全检查": "安全检查",
    "CapabilityEvolver": "能力进化诊断",
    "Rule-Refiner": "规则提炼",
    "Pre-Market-Check": "盘前预检",
    "Daily-Evening-Report": "晚报",
}


def parse_ts(ts_val):
    """统一解析时间戳，返回datetime对象"""
    if not ts_val:
        return None
    if isinstance(ts_val, (int, float)):
        return datetime.datetime.fromtimestamp(ts_val / 1000, tz=datetime.timezone.utc)
    if isinstance(ts_val, str):
        try:
            return datetime.datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
        except:
            return None
    return None


def is_system_message(text):
    if not text:
        return True
    upper = text.upper()
    for kw in SYSTEM_KEYWORDS:
        if kw.upper() in upper:
            return True
    return False


def identify_cron_task(text):
    """从文本中识别Cron任务名"""
    if not text:
        return None
    for key, name in CRON_TASKS.items():
        if key.lower() in text.lower():
            return name
    return None


def analyze_session(filepath):
    """分析单个Session文件"""
    result = {
        "file": os.path.basename(filepath),
        "start_time": None,
        "end_time": None,
        "duration_min": 0,
        "total_tokens": 0,
        "user_messages": 0,
        "assistant_messages": 0,
        "tool_calls": 0,
        "errors": 0,
        "is_cron": False,
        "cron_task_name": None,
        "user_texts": [],
        "assistant_texts": [],
        "topics": [],
        "has_error": False,
        "error_messages": [],
    }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except:
        return result

    # 解析第一行（session头）
    first = json.loads(lines[0]) if lines else {}
    result["start_time"] = parse_ts(first.get("timestamp"))

    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except:
            continue

        msg_type = obj.get("type", "")
        if msg_type != "message":
            continue

        msg = obj.get("message", {})
        role = msg.get("role", "")
        content = msg.get("content", "")
        if isinstance(content, list):
            texts = []
            for c in content:
                if isinstance(c, dict):
                    t = c.get("text", "")
                    if t:
                        texts.append(t)
            content = "\n".join(texts)

        ts = parse_ts(obj.get("timestamp"))
        if ts and (not result["end_time"] or ts > result["end_time"]):
            result["end_time"] = ts

        # usage可能在message内部
        msg_usage = msg.get("usage", {}) if isinstance(msg, dict) else {}
        usage = msg_usage or obj.get("usage", {})
        tokens = usage.get("totalTokens", 0) or 0
        result["total_tokens"] += tokens

        if role == "user":
            result["user_messages"] += 1
            if content and not is_system_message(content):
                result["user_texts"].append(content[:200])
        elif role == "assistant":
            result["assistant_messages"] += 1
            if content:
                result["assistant_texts"].append(content[:200])
        elif role == "toolResult":
            result["tool_calls"] += 1

        # 检测错误
        if content and ("error" in content.lower() or "exception" in content.lower()
                        or "failed" in content.lower() or "超时" in content
                        or "失败" in content or "报错" in content):
            if "HEARTBEAT_OK" not in content and "NO_REPLY" not in content:
                result["has_error"] = True
                result["error_messages"].append(content[:150])

    if result["start_time"] and result["end_time"]:
        delta = result["end_time"] - result["start_time"]
        result["duration_min"] = round(delta.total_seconds() / 60, 1)

    # 识别Cron任务
    all_text = " ".join(result["user_texts"] + result["assistant_texts"])
    task_name = identify_cron_task(all_text)
    if task_name:
        result["is_cron"] = True
        result["cron_task_name"] = task_name
    elif result["user_messages"] == 0 and result["assistant_messages"] <= 3:
        # 无用户输入、短对话 → 可能是Cron
        result["is_cron"] = True

    return result


def get_date_str():
    """获取分析的目标日期"""
    if len(sys.argv) > 2 and sys.argv[1] == "--date":
        return sys.argv[2]
    return datetime.date.today().isoformat()


def load_state():
    """加载上次分析的日期偏移"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"last_date": ""}


def save_state(date_str):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump({"last_date": date_str}, f)


def save_to_obsidian(title, content, category="系统"):
    """保存到Obsidian"""
    from obsidian_save import save_note
    return save_note(title, content, category)


def main():
    date_str = get_date_str()
    state = load_state()

    # 收集当天所有Session文件
    all_files = sorted(glob.glob(os.path.join(SESSION_DIR, "*.jsonl")))
    target_files = []

    for f in all_files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                first = json.loads(fh.readline())
            ts = parse_ts(first.get("timestamp"))
            if ts and ts.strftime("%Y-%m-%d") == date_str:
                target_files.append(f)
        except:
            continue

    if not target_files:
        print(f"⚠️ {date_str} 没有Session记录")
        return

    print(f"📊 分析 {date_str}，共 {len(target_files)} 个Session")

    # 逐个分析
    sessions = []
    for f in target_files:
        sa = analyze_session(f)
        sessions.append(sa)

    # 统计
    total_tokens = sum(s["total_tokens"] for s in sessions)
    cron_sessions = [s for s in sessions if s["is_cron"]]
    dialog_sessions = [s for s in sessions if not s["is_cron"]]
    error_sessions = [s for s in sessions if s["has_error"]]

    # Cron任务统计
    cron_status = defaultdict(lambda: {"count": 0, "errors": 0, "tokens": 0})
    for s in cron_sessions:
        name = s["cron_task_name"] or "未识别任务"
        cron_status[name]["count"] += 1
        cron_status[name]["tokens"] += s["total_tokens"]
        if s["has_error"]:
            cron_status[name]["errors"] += 1

    # 对话主题提取
    dialog_topics = []
    for s in dialog_sessions:
        for t in s["user_texts"]:
            dialog_topics.append(t[:80])

    # 构建报告
    report = []
    report.append(f"# 📊 Session分析报告 — {date_str}")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## 一、总体概览")
    report.append("")
    report.append(f"| 指标 | 数值 |")
    report.append(f"|------|------|")
    report.append(f"| Session总数 | {len(sessions)} |")
    report.append(f"| 对话Session | {len(dialog_sessions)} |")
    report.append(f"| Cron任务Session | {len(cron_sessions)} |")
    report.append(f"| 异常Session | {len(error_sessions)} |")
    report.append(f"| 总Token消耗 | {total_tokens:,} |")
    report.append(f"| 平均Token/Session | {total_tokens // max(len(sessions), 1):,} |")
    report.append("")

    # 异常列表
    if error_sessions:
        report.append("## ⚠️ 异常Session")
        report.append("")
        for s in error_sessions[:10]:
            task = s["cron_task_name"] or "对话"
            report.append(f"- **{task}** ({s['file'][:8]}): {s['error_messages'][0][:100] if s['error_messages'] else '未知错误'}")
        report.append("")

    # Cron任务执行情况
    report.append("## 二、Cron任务执行")
    report.append("")
    report.append("| 任务 | 执行次数 | 异常 | Token消耗 |")
    report.append("|------|---------|------|----------|")
    for name in sorted(cron_status.keys()):
        st = cron_status[name]
        err_mark = f"⚠️{st['errors']}" if st['errors'] else "✅"
        report.append(f"| {name} | {st['count']} | {err_mark} | {st['tokens']:,} |")
    report.append("")

    # 对话摘要
    if dialog_topics:
        report.append("## 三、对话摘要")
        report.append("")
        for i, t in enumerate(dialog_topics[:20]):
            report.append(f"{i+1}. {t}")
        if len(dialog_topics) > 20:
            report.append(f"... 还有 {len(dialog_topics) - 20} 条")
        report.append("")

    # Token趋势
    report.append("## 四、Token消耗")
    report.append("")
    report.append(f"- 今日总消耗: **{total_tokens:,}**")
    report.append(f"- Cron任务消耗: **{sum(s['total_tokens'] for s in cron_sessions):,}**")
    report.append(f"- 对话消耗: **{sum(s['total_tokens'] for s in dialog_sessions):,}**")
    report.append("")

    # 健康度
    health = "✅ 健康" if len(error_sessions) == 0 else \
             "⚠️ 轻微异常" if len(error_sessions) <= 3 else \
             "🔴 需要关注"
    report.append("## 五、健康度评估")
    report.append("")
    report.append(f"**{health}**")
    if error_sessions:
        report.append(f"- {len(error_sessions)} 个Session存在异常")
        report.append(f"- 建议: 检查异常任务，确认是否需要修复")
    report.append("")

    report.append("---")
    report.append(f"_由 可悦🌸 于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} 自动生成_")

    report_text = "\n".join(report)

    # 保存到Obsidian
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from obsidian_save import save_note
        fp = save_note(f"Session分析报告_{date_str}", report_text, "系统")
        print(f"✅ 已保存: {fp}")
    except Exception as e:
        print(f"⚠️ 保存到Obsidian失败: {e}")
        print(f"\n--- 报告预览 ---\n{report_text[:500]}")

    # 保存状态
    save_state(date_str)

    # 输出给Cron回传
    print(f"\n📋 报告摘要: {len(sessions)}个Session, {len(error_sessions)}个异常, {total_tokens:,} tokens")


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()