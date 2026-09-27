"""
log_audit.py - 每日任务日志审计 + 自我学习总结
检查Cron任务执行情况 vs 日志记录情况，发现"任务跑了但没写日志"的问题
从当日错误中提取新的踩坑点，更新到 corrections.md（需确认）

每天运行两次：
    09:05 检查昨日（隔夜积累的问题）
    22:00 检查当日（当日工作结束前的自我总结）
"""
import os
import sys
import json
import re
from datetime import datetime, timedelta
import io

# ============================================================
# 自记录日志（确保即使绕过 run_with_log.py 也能写入任务日志）
# ============================================================
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from task_logger import log as _task_log
    _HAS_LOGGER = True
except ImportError:
    _HAS_LOGGER = False

TASK_NAME = "LOG-日志审计-每日检查"
TASK_SYSTEM = "main"

def _auto_log(status, detail="", error_msg="", duration_ms=None):
    """自动记录任务日志，失败时静默忽略"""
    if not _HAS_LOGGER:
        return
    try:
        _task_log(TASK_NAME, TASK_SYSTEM, status=status, detail=detail,
                  error_msg=error_msg, duration_ms=duration_ms)
    except Exception:
        pass

# ============================================================
# 配置
# ============================================================
WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"
LOG_BASE = r"C:\Users\Administrator\.openclaw\workspace\memory\日志\task"
REPORT_DIR = os.path.join(LOG_BASE, "audit")
os.makedirs(REPORT_DIR, exist_ok=True)

SYSTEMS = ["main", "novel", "investment", "social", "math", "weixin"]

# corrections.md 路径（各系统）
CORRECTIONS_PATHS = {
    "main": os.path.join(WORKSPACE, "corrections.md"),
    "novel": os.path.join(WORKSPACE, "workspace-novel", "memory", "corrections.md"),
    "investment": os.path.join(WORKSPACE, "workspace-investment", "memory", "corrections.md"),
    "social": os.path.join(WORKSPACE, "workspace-social", "memory", "corrections.md"),
    "math": os.path.join(WORKSPACE, "workspace-math", "memory", "corrections.md"),
    "weixin": os.path.join(WORKSPACE, "workspace-weixin", "memory", "corrections.md"),
}

# ============================================================
# 读取日志
# ============================================================
def read_day_logs(date_str):
    """读取指定日期的所有系统日志"""
    log_path = os.path.join(LOG_BASE, date_str[:4], date_str[4:6], "all", f"{date_str}.jsonl")
    if not os.path.exists(log_path):
        return []

    records = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records

# ============================================================
# 读取 corrections.md 已有记录（用于去重）
# ============================================================
def load_corrections():
    """加载所有系统的 corrections.md，建立问题关键词集合"""
    known_issues = {}  # system -> set of issue signatures
    for sys_name, path in CORRECTIONS_PATHS.items():
        if not os.path.exists(path):
            known_issues[sys_name] = set()
            continue

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取问题标题（用于去重识别）
        signatures = set()
        # 匹配 "## 问题描述" 或 "### xxx踩坑" 等标题模式
        titles = re.findall(r'#{1,3}\s+[^#\n].+', content)
        for t in titles:
            sig = t.strip().lower()
            if len(sig) > 5:
                signatures.add(sig)
        known_issues[sys_name] = signatures

    return known_issues

# ============================================================
# 系统推断
# ============================================================
def infer_system(task_name):
    """根据任务名推断系统"""
    name_lower = task_name.lower()
    if "novel" in name_lower or "小说" in name_lower:
        return "novel"
    if "inv" in name_lower or "投资" in name_lower or "策略" in name_lower:
        return "investment"
    if "social" in name_lower or "自媒体" in name_lower:
        return "social"
    if "math" in name_lower or "数学" in name_lower or "manim" in name_lower:
        return "math"
    if "wx" in name_lower or "weixin" in name_lower or "微信" in name_lower:
        return "weixin"
    return "main"

# ============================================================
# Cron 任务列表
# ============================================================
def get_cron_jobs():
    """通过 openclaw cron list 获取任务名列表（二进制模式，避免 GBK 解码崩溃）"""
    import subprocess
    openclaw_exe = r"C:\Users\Administrator\AppData\Roaming\npm\openclaw.cmd"
    try:
        result = subprocess.run(
            [openclaw_exe, "cron", "list", "--json"],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        stdout = result.stdout.decode("utf-8", errors="replace")
        data = json.loads(stdout)
        return [(j["name"], j.get("id", "")) for j in data.get("jobs", []) if j.get("enabled", True)]
    except subprocess.TimeoutExpired:
        print("[审计] 警告: openclaw cron list 超时，跳过 cron 审计")
        return []
    except Exception:
        return []

# ============================================================
# 审计逻辑
# ============================================================
def audit_day(date_str):
    """
    审计指定日期的日志情况。
    返回 (ok_tasks, missing_tasks, error_records, skipped_records)
    - error_records/skipped_records: 从 task_logger 日志中提取的 ERROR/SKIPPED 记录
    """
    logs = read_day_logs(date_str)

    # task+system -> status
    logged_tasks = {}
    for r in logs:
        key = (r.get("task", ""), r.get("system", ""))
        logged_tasks[key] = r.get("status", "OK")

    cron_jobs = get_cron_jobs()
    ok_tasks = []
    missing_tasks = []
    error_records = []
    skipped_records = []

    for task_name, _ in cron_jobs:
        sys_name = infer_system(task_name)
        key = (task_name, sys_name)
        if key in logged_tasks:
            status = logged_tasks[key]
            if status == "OK":
                ok_tasks.append(task_name)
            elif status == "SKIPPED":
                skipped_records.append((task_name, logs[[i for i, r in enumerate(logs) if r.get("task") == task_name][0]]))
            else:
                # 找出对应的完整日志记录
                for r in logs:
                    if r.get("task") == task_name and r.get("status") != "OK":
                        error_records.append((task_name, r))
                        break
        else:
            missing_tasks.append(task_name)

    return ok_tasks, missing_tasks, error_records, skipped_records

# ============================================================
# 学习总结：从错误中提取新的踩坑点
# ============================================================
def extract_learning(date_str, error_records, skipped_records, known_issues):
    """
    从当日错误/skipped 记录中提取可学习的内容。
    返回 (new_issues, known_issues_matched)
    """
    new_issues = []   # [(task, error_msg, detail)]
    known_matches = []  # [(task, error_msg, known_sig)]

    for task_name, record in error_records + skipped_records:
        sys_name = record.get("system", infer_system(task_name))
        error_msg = record.get("error", "")
        detail = record.get("detail", "") or record.get("task", "")

        # 用错误信息的前50字符作为签名
        sig = error_msg[:80].lower().strip() if error_msg else detail[:80].lower()

        # 检查是否已知
        matched = False
        if sys_name in known_issues:
            for known_sig in known_issues[sys_name]:
                # 简单相似度：是否有共同关键词
                if any(kw in sig for kw in known_sig.split() if len(kw) > 4):
                    known_matches.append((task_name, error_msg, known_sig))
                    matched = True
                    break

        if not matched:
            new_issues.append((task_name, error_msg, record.get("detail", "")))

    return new_issues, known_matches

# ============================================================
# 报告生成
# ============================================================
def generate_report(date_str, for_today=False):
    """
    生成完整的审计+学习报告。
    - for_today=True: 生成当日报告（22:00用，给出实时建议）
    - for_today=False: 生成昨日报告（09:05用，总结隔夜问题）
    """
    label = "今日" if for_today else "昨日"
    ok_tasks, missing_tasks, error_records, skipped_records = audit_day(date_str)
    known_issues = load_corrections()
    new_issues, known_matches = extract_learning(date_str, error_records, skipped_records, known_issues)

    # 时间戳
    date_display = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    report_lines = [
        f"# 任务日志审计报告 - {date_display}（{label}）",
        "",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        f"## 一、概览",
        f"- ✅ 正常: {len(ok_tasks)} 个任务",
        f"- ⚠️ 出错: {len(error_records)} 个任务",
        f"- ⏭️ 跳过: {len(skipped_records)} 个任务",
        f"- ❌ 无日志: {len(missing_tasks)} 个任务",
        f"- 🆕 新踩坑: {len(new_issues)} 个",
        f"- 🔁 已知问题: {len(known_matches)} 个",
        "",
    ]

    # 二、正常任务
    if ok_tasks:
        report_lines.extend([
            "## 二、✅ 正常任务",
            f"共 {len(ok_tasks)} 个任务执行正常",
            "",
        ])

    # 三、出错任务
    if error_records:
        report_lines.extend([
            "## 三、⚠️ 出错任务",
            "",
        ])
        for task_name, record in error_records:
            error_msg = record.get("error", "未知错误")
            duration = record.get("duration_ms", 0)
            detail = record.get("detail", "")
            report_lines.append(f"### {task_name}")
            report_lines.append(f"- **错误**: {error_msg}")
            if duration:
                report_lines.append(f"- **耗时**: {duration/1000:.1f}s")
            if detail and len(detail) < 300:
                report_lines.append(f"- **详情**: {detail}")
            report_lines.append("")
        report_lines.append("")

    # 四、跳过任务
    if skipped_records:
        report_lines.extend([
            "## 四、⏭️ 跳过任务",
            "",
        ])
        for task_name, record in skipped_records:
            report_lines.append(f"- {task_name}")
        report_lines.extend(["", ""])

    # 五、无日志任务
    if missing_tasks:
        report_lines.extend([
            "## 五、❌ 无日志任务",
            "",
            "以下任务在 Cron 中配置了，但未记录任务日志（可能超时/未触发/脚本问题）：",
            "",
        ])
        for t in sorted(missing_tasks):
            report_lines.append(f"- {t}")
        report_lines.extend([
            "",
            "**修复方法**: 将 Cron message 改为 `python run_with_log.py \"任务名\" \"系统\" \"脚本路径\"`",
            "",
        ])

    # 六、学习总结（核心新增）
    report_lines.extend([
        "## 六、📝 每日学习总结",
        "",
    ])

    if known_matches:
        report_lines.append("### 🔁 已知问题（已有记录，持续监控）")
        for task_name, error_msg, known_sig in known_matches:
            report_lines.append(f"- [{task_name}] {error_msg}")
            report_lines.append(f"  → 已在 corrections.md 有记录: {known_sig[:60]}")
        report_lines.append("")

    if new_issues:
        report_lines.append("### 🆕 新发现踩坑（建议写入 corrections.md）")
        report_lines.append("")
        for task_name, error_msg, detail in new_issues:
            report_lines.append(f"**{task_name}**")
            report_lines.append(f"- 错误: {error_msg}")
            if detail and len(detail) < 500:
                report_lines.append(f"- 详情: {detail[:200]}")
            report_lines.append("")
        report_lines.append("**操作建议**: 以上新踩坑点建议由主系统确认后写入 `corrections.md`，格式：")
        report_lines.append("")
        report_lines.append("```markdown")
        report_lines.append("## YYYY-MM-DD 新踩坑标题")
        report_lines.append("")
        report_lines.append("### 问题")
        report_lines.append("描述...")
        report_lines.append("")
        report_lines.append("### 根因")
        report_lines.append("...")
        report_lines.append("")
        report_lines.append("### 固化措施")
        report_lines.append("- [ ] ...")
        report_lines.append("```")
        report_lines.append("")
    else:
        report_lines.append("### ✅ 今日无新踩坑")
        report_lines.append("所有错误均在 corrections.md 中有记录，持续监控中。")
        report_lines.append("")

    # 七、明日待办
    report_lines.extend(["## 七、📋 明日待办", ""])
    if new_issues:
        report_lines.append("1. 确认并写入新踩坑点到 corrections.md")
    if missing_tasks:
        report_lines.append(f"2. 修复 {len(missing_tasks)} 个无日志任务的 Cron 配置")
    if error_records:
        report_lines.append(f"3. 处理 {len(error_records)} 个出错任务")
    if not new_issues and not missing_tasks and not error_records:
        report_lines.append("✅ 无待办事项，系统运行正常")
    report_lines.append("")

    content = "\n".join(report_lines)
    report_path = os.path.join(REPORT_DIR, f"audit_{date_str}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    return report_path, {
        "ok": len(ok_tasks),
        "error": len(error_records),
        "skipped": len(skipped_records),
        "missing": len(missing_tasks),
        "new_issues": len(new_issues),
        "known": len(known_matches),
    }

# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    _start = datetime.now()

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    import sys

    # 用法: python log_audit.py [YYYYMMDD] [--today]
    # 默认审计昨天；--today 审计今日
    date_str = None
    for_today = False

    for arg in sys.argv[1:]:
        if arg == "--today":
            for_today = True
        elif arg.isdigit() and len(arg) == 8:
            date_str = arg
        elif arg in ("-h", "--help"):
            print("用法: python log_audit.py [YYYYMMDD] [--today]")
            sys.exit(0)

    if date_str is None:
        if for_today:
            date_str = datetime.now().strftime("%Y%m%d")
        else:
            date_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

    label = "今日" if for_today else "昨日"
    print(f"[审计] 检查 {label}（{date_str}）的任务日志...")

    report_path, stats = generate_report(date_str, for_today=for_today)

    print(f"[审计] 报告已生成: {report_path}")
    print(f"[审计] 结果: 正常{stats['ok']} | 出错{stats['error']} | 跳过{stats['skipped']} | 无日志{stats['missing']} | 新踩坑{stats['new_issues']}")

    # 自动记录任务日志
    _dur = (datetime.now() - _start).total_seconds() * 1000
    has_issues = stats["error"] > 0 or stats["missing"] > 0 or stats["new_issues"] > 0
    _auto_log("OK" if not has_issues else "ERROR",
              detail=f"正常{stats['ok']} 出错{stats['error']} 无日志{stats['missing']}",
              duration_ms=_dur)

    # 退出码：有问题或新踩坑则非0（供 Cron 判断是否通知）
    sys.exit(1 if has_issues else 0)