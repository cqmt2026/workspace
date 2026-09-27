# -*- coding: utf-8 -*-
"""
weekly_capability_evolver.py
每周诊断分析：分析上周日志，检测错误模式并生成改进提案
运行于隔离cron session，作为 Capability Evolver 的本地 Python 实现

分析内容：
- 工作日志中的错误/问题记录
- 系统状态变化
- 重复出现的问题模式
- 效率瓶颈
"""
import os
import re
import glob
from datetime import datetime, timedelta
from collections import defaultdict
import json
import io

WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"
LOG_DIR = os.path.join(WORKSPACE, "memory", "日志")


def get_last_week_logs():
    """获取上周（周一到周日）的日志文件"""
    today = datetime.now()
    # 找到本周一
    days_since_monday = today.weekday()
    this_monday = today - timedelta(days=days_since_monday)
    # 上周一
    last_monday = this_monday - timedelta(days=7)
    # 上周日
    last_sunday = last_monday + timedelta(days=6)

    log_files = []
    for f in glob.glob(os.path.join(LOG_DIR, "2026-*.md")):
        basename = os.path.basename(f)
        match = re.match(r"2026-(\d{2})-(\d{2})", basename)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            try:
                file_date = datetime(2026, month, day)
                if last_monday <= file_date <= last_sunday:
                    log_files.append(f)
            except ValueError:
                continue
        # 也包含本周一（当天诊断）
        match2 = re.match(r"2026-(\d{2})-(\d{2})", basename)
        if match2:
            month, day = int(match2.group(1)), int(match2.group(2))
            try:
                file_date = datetime(2026, month, day)
                if file_date == today.replace(hour=0, minute=0, second=0, microsecond=0):
                    log_files.append(f)
            except ValueError:
                continue

    log_files.sort()
    return log_files


def extract_error_patterns(content):
    """从日志内容中提取错误/问题模式"""
    patterns = []

    # 匹配问题描述
    error_keywords = [
        r"问题[:：]\s*(.+?)(?=\n##|\Z)",
        r"错误[:：]\s*(.+?)(?=\n##|\Z)",
        r"失败[:：]\s*(.+?)(?=\n##|\Z)",
        r"bug[:：]\s*(.+?)(?=\n##|\Z)",
        r"(?:无法|不能|失败|错误|问题)(.+?)。",
    ]

    for kw in error_keywords:
        for m in re.finditer(kw, content, re.IGNORECASE):
            text = m.group(1).strip()
            if len(text) > 5:
                patterns.append({
                    "keyword": kw[:20],
                    "text": text[:200],
                    "match": m.group(0)[:100]
                })

    return patterns


def extract_fix_records(content):
    """提取修复记录"""
    fixes = []
    fix_patterns = [
        r"(?:修复|fix)[:：]\s*(.+?)(?=\n##|\n\n|\Z)",
        r"✅\s*(?:完成|修复|已解决)[:：]?\s*(.+?)(?=\n##|\n\n|\Z)",
    ]
    for kw in fix_patterns:
        for m in re.finditer(kw, content, re.IGNORECASE):
            text = m.group(1).strip()
            if len(text) > 3:
                fixes.append(text[:200])
    return fixes


def detect_repeated_patterns(all_errors):
    """检测重复出现的模式"""
    pattern_counts = defaultdict(int)
    for err in all_errors:
        # 用前50字符作为模式标识
        key = err["text"][:50].lower()
        pattern_counts[key] += 1

    repeated = []
    for pattern, count in pattern_counts.items():
        if count >= 2:
            repeated.append({
                "pattern": pattern,
                "count": count,
                "severity": "high" if count >= 3 else "medium"
            })
    return repeated


def compute_health_score(errors, fixes, total_logs):
    """计算健康分数 0-100"""
    if total_logs == 0:
        return 100

    # 错误频率
    error_rate = len(errors) / total_logs
    # 修复率
    fix_rate = len(fixes) / max(len(errors), 1)
    # 重复错误惩罚
    repeated_count = sum(1 for p in errors if len(p["text"]) < 100)
    repeat_penalty = min(repeated_count * 5, 25)

    base_score = 100
    score = base_score - (error_rate * 40) - repeat_penalty + (fix_rate * 20)
    return max(0, min(100, round(score)))


def generate_recommendations(errors, repeated, health_score):
    """生成改进建议"""
    recs = []

    if health_score < 70:
        recs.append({
            "priority": "critical",
            "category": "reliability",
            "description": f"健康分数{health_score}低于70，系统存在较多问题，建议优先修复重复出现的问题",
            "suggested_approach": "先解决最高频的重复问题，再处理其他错误"
        })

    # 按问题类别分组
    categories = {
        "token": [],
        "math": [],
        "video": [],
        "data": [],
        "workflow": [],
        "other": []
    }

    for err in errors:
        text = err["text"].lower()
        if any(k in text for k in ["token", "compaction", "session"]):
            categories["token"].append(err)
        elif any(k in text for k in ["数学", "计算", "公式"]):
            categories["math"].append(err)
        elif any(k in text for k in ["视频", "渲染", "ffmpeg", "音频", "mp3"]):
            categories["video"].append(err)
        elif any(k in text for k in ["数据", "获取", "api", "采集"]):
            categories["data"].append(err)
        elif any(k in text for k in ["工作流", "流程", "规划"]):
            categories["workflow"].append(err)
        else:
            categories["other"].append(err)

    for cat, items in categories.items():
        if len(items) >= 2:
            recs.append({
                "priority": "high",
                "category": cat,
                "description": f"{cat}类问题出现{len(items)}次",
                "suggested_approach": f"针对{cat}类问题建立标准流程和验证机制"
            })

    if repeated:
        top_repeated = sorted(repeated, key=lambda x: x["count"], reverse=True)[:3]
        for r in top_repeated:
            recs.append({
                "priority": "high",
                "category": "repeated_error",
                "description": f"重复问题「{r['pattern'][:30]}...」出现{r['count']}次",
                "suggested_approach": "找出根本原因，一次性解决，避免反复修复"
            })

    return recs


def main():
    print("=" * 60)
    print("Capability Evolver - 每周诊断")
    print(f"分析周期: 上周 (2026-06-08 ~ 2026-06-15)")
    print("=" * 60)

    # 获取上周日志
    log_files = get_last_week_logs()
    if not log_files:
        log_files = glob.glob(os.path.join(LOG_DIR, "2026-*.md"))
        log_files.sort()
        # 取最近一周
        log_files = log_files[-7:]

    print(f"\n📂 分析日志文件: {len(log_files)}个")
    for f in log_files:
        print(f"  - {os.path.basename(f)}")

    # 读取所有日志内容
    all_content = ""
    for f in log_files:
        with open(f, "r", encoding="utf-8", errors="replace") as fp:
            content = fp.read()
            all_content += f"\n\n=== {os.path.basename(f)} ===\n\n" + content

    total_logs = len(log_files)

    # 提取错误模式
    errors = extract_error_patterns(all_content)
    fixes = extract_fix_records(all_content)
    repeated = detect_repeated_patterns(errors)

    # 计算健康分数
    health_score = compute_health_score(errors, fixes, total_logs)

    print(f"\n📊 分析结果:")
    print(f"  - 发现问题记录: {len(errors)}条")
    print(f"  - 修复记录: {len(fixes)}条")
    print(f"  - 重复模式: {len(repeated)}个")
    print(f"  - 健康分数: {health_score}/100")

    if repeated:
        print(f"\n🔁 重复模式 (top 5):")
        for r in sorted(repeated, key=lambda x: x["count"], reverse=True)[:5]:
            print(f"  [{r['severity']}] {r['pattern'][:50]}... x{r['count']}")

    # 生成建议
    recommendations = generate_recommendations(errors, repeated, health_score)

    print(f"\n💡 改进建议 ({len(recommendations)}条):")
    for i, rec in enumerate(recommendations[:10], 1):
        print(f"  {i}. [{rec['priority']}] {rec['category']}: {rec['description']}")
        print(f"     → {rec['suggested_approach']}")

    # 输出结构化报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "period": "2026-06-08 ~ 2026-06-15",
        "health_score": health_score,
        "summary": {
            "total_logs": total_logs,
            "error_count": len(errors),
            "fix_count": len(fixes),
            "unique_patterns": len(repeated)
        },
        "patterns": repeated,
        "recommendations": recommendations
    }

    # 保存报告
    report_path = os.path.join(WORKSPACE, "memory", "系统", "capability_evolver_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2)

    md_report = f"""# Capability Evolver 每周诊断报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**分析周期**: 2026-06-08 ~ 2026-06-15

---

## 📊 健康分数

**{health_score}/100** {"✅ 良好" if health_score >= 80 else "⚠️ 一般" if health_score >= 60 else "❌ 需改进"}

---

## 📈 统计数据

| 指标 | 数值 |
|------|------|
| 分析日志数 | {total_logs} |
| 发现问题 | {len(errors)}条 |
| 修复记录 | {len(fixes)}条 |
| 重复模式 | {len(repeated)}个 |

---

## 🔁 重复出现的问题模式

"""
    if repeated:
        for r in sorted(repeated, key=lambda x: x["count"], reverse=True):
            md_report += f"- **{r['pattern'][:60]}** ×{r['count']}次 [{r['severity']}]\n"
    else:
        md_report += "未发现重复问题。\n"

    md_report += "\n---\n\n## 💡 改进建议\n\n"
    for i, rec in enumerate(recommendations[:10], 1):
        md_report += f"### {i}. [{rec['priority'].upper()}] {rec['category']}\n"
        md_report += f"**问题**: {rec['description']}\n\n"
        md_report += f"**建议方案**: {rec['suggested_approach']}\n\n"

    md_report_path = os.path.join(WORKSPACE, "memory", "系统", "capability_evolver_report.md")
    with open(md_report_path, "w", encoding="utf-8") as fp:
        fp.write(md_report)

    print(f"\n✅ 报告已保存:")
    print(f"  - JSON: {report_path}")
    print(f"  - Markdown: {md_report_path}")
    print("=" * 60)

    return health_score


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()