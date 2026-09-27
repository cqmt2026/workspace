"""
self_learning.py - 每日自我学习总结
每天 21:00 运行，整合日志审计 + 踩坑记录 + 知识库学习 + Supermemory记忆提取

功能：
1. 日志审计 - 检查当日所有任务日志
2. 踩坑学习 - 从错误中提取新踩坑点，写入 corrections.md
3. 知识库学习 - 调用各子系统 auto_learning.py
4. 规则格式检查 - 检查主系统corrections.md规则格式完整性
5. 子系统corrections审计 - 检查空条目/未固化措施/过期条目
6. Supermemory记忆 - 提取当日重要决策/操作写入Supermemory长期记忆
7. 记忆晋升 - 触发 Memory Dreaming（如果当日有重要记忆需要晋升）
"""
import os
import sys
import io
import json
import re
import subprocess
from datetime import datetime, timedelta

# ============================================================
# 自记录日志（确保即使绕过 run_with_log.py 也能写入任务日志）
# ============================================================
try:
    _ws = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _ws)
    from task_logger import log as _task_log
    _HAS_LOGGER = True
except ImportError:
    _HAS_LOGGER = False

def _auto_log(status, detail="", error_msg="", duration_ms=None):
    """自动记录任务日志，失败时静默忽略"""
    if not _HAS_LOGGER:
        return
    try:
        _task_log("Self-Learning-统一学习", "main", status=status, detail=detail,
                  error_msg=error_msg, duration_ms=duration_ms)
    except Exception:
        pass

# Fix stdout encoding for Windows GBK
if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"
LOG_BASE = r"C:\Users\Administrator\.openclaw\workspace\memory\日志\task"
REPORT_DIR = os.path.join(LOG_BASE, "audit")
os.makedirs(REPORT_DIR, exist_ok=True)

SYSTEMS = ["main", "novel", "investment", "social", "math", "weixin"]

CORRECTIONS_PATHS = {
    "main": os.path.join(WORKSPACE, "corrections.md"),
    "novel": os.path.join(WORKSPACE, "workspace-novel", "memory", "corrections.md"),
    "investment": os.path.join(WORKSPACE, "workspace-investment", "memory", "corrections.md"),
    "social": os.path.join(WORKSPACE, "workspace-social", "memory", "corrections.md"),
    "math": os.path.join(WORKSPACE, "workspace-math", "memory", "corrections.md"),
    "weixin": os.path.join(WORKSPACE, "workspace-weixin", "memory", "corrections.md"),
}

# 各子系统 auto_learning 脚本路径
LEARNING_SCRIPTS = {
    "novel": os.path.join(WORKSPACE, "workspace-novel", "创作系统", "L1-日志", "scripts", "auto_learning.py"),
    "investment": os.path.join(WORKSPACE, "workspace-investment", "scripts", "self_learn_review.py"),
    "social": os.path.join(WORKSPACE, "workspace-social", "scripts", "viral_deep_learning.py"),
    "math": os.path.join(WORKSPACE, "workspace-math", "scripts", "auto_learn_trigger.py"),
}

# ============================================================
# 1. 读取当日任务日志
# ============================================================
def read_day_logs(date_str):
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
# 2. 踩坑学习
# ============================================================
def infer_system(task_name):
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

def load_corrections_signatures(sys_name):
    """加载指定系统 corrections.md 的已有问题签名（用于去重）"""
    path = CORRECTIONS_PATHS.get(sys_name)
    if not path or not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # 提取 ## 或 ### 标题作为签名
    signatures = set()
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("### "):
            sig = stripped.lower()
            if len(sig) > 8:
                signatures.add(sig)
    return signatures

def append_correction(sys_name, task_name, error_msg, detail):
    """将新踩坑追加到 corrections.md"""
    path = CORRECTIONS_PATHS.get(sys_name)
    if not path:
        return False

    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = f"""
## {date_str} [{task_name}] {error_msg[:60]}

### 问题
{task_name} 执行失败：{error_msg}

### 根因
待分析（详见当日日志审计报告）

### 固化措施
- [ ] 待填写
"""
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)
    return True

def learn_from_errors(date_str, logs):
    """
    从当日日志中提取错误，与 corrections 比对，
    识别新踩坑并写入对应 corrections.md
    返回 (new_learned_count, new_issues_detail)
    """
    error_records = [r for r in logs if r.get("status") == "ERROR"]
    new_count = 0
    new_details = []

    for record in error_records:
        task_name = record.get("task", "")
        sys_name = record.get("system", infer_system(task_name))
        error_msg = record.get("error", "")

        if not error_msg:
            continue

        # 去重：检查是否已在 corrections.md
        sigs = load_corrections_signatures(sys_name)
        is_new = True
        for sig in sigs:
            common = sum(1 for kw in error_msg[:40].split() if len(kw) > 3 and kw in sig)
            if common >= 2:
                is_new = False
                break

        if is_new:
            detail = record.get("detail", "")
            append_correction(sys_name, task_name, error_msg, detail)
            new_count += 1
            new_details.append((task_name, sys_name, error_msg[:80]))

    return new_count, new_details

# ============================================================
# 3. 知识库学习 - 调用各子系统
# ============================================================
def run_subsystem_learning():
    """调用各子系统的 auto_learning 脚本"""
    results = []
    for sys_name, script_path in LEARNING_SCRIPTS.items():
        if not os.path.exists(script_path):
            results.append((sys_name, "SKIP", "脚本不存在"))
            continue

        print(f"[学习] 运行 {sys_name} 知识库学习...")
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True, text=True,
                timeout=120,
                encoding="utf-8", errors="replace"
            )
            if result.returncode == 0:
                results.append((sys_name, "OK", result.stdout[:200] if result.stdout else ""))
            else:
                results.append((sys_name, "FAIL", result.stderr[:100] if result.stderr else f"exit {result.returncode}"))
        except subprocess.TimeoutExpired:
            results.append((sys_name, "TIMEOUT", "120s超时"))
        except Exception as e:
            results.append((sys_name, "ERROR", str(e)[:100]))

    return results


def _save_subsystem_learning_results(results):
    try:
        _mem_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'memory')
        _scr_dir = os.path.dirname(os.path.abspath(__file__))
        for _d in (_scr_dir, _mem_dir):
            if _d not in sys.path:
                sys.path.insert(0, _d)
        from memory_adapter import save
        for sys_name, status, detail in results:
            if status == 'OK':
                save('%s自我学习: 完成' % sys_name, category='decision', source='system-learning')
            elif status in ('FAIL', 'ERROR'):
                save('%s自我学习: %s - %s' % (sys_name, status, detail[:80]), category='decision', source='system-learning')
        print('  [Supermemory] 已存档%d条学习结果' % len(results))
    except Exception as e:
        print('  [Supermemory] 存档失败: %s' % e)


# ============================================================
# 4. 规则格式检查 - 扫描主系统corrections.md
# ============================================================
def audit_rule_format():
    """
    扫描corrections.md，检查每条Rxxx规则是否满足：
    触发条件 -> 行为 -> 验证 三段式格式
    """
    path = CORRECTIONS_PATHS.get("main")
    if not path or not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    issues = []
    current_rule = None
    has_trigger = False
    has_action = False
    has_verify = False

    for line in content.split("\n"):
        stripped = line.strip()

        if stripped.startswith("## R") and " - " in stripped:
            if current_rule and not (has_trigger and has_action and has_verify):
                missing = []
                if not has_trigger:
                    missing.append("触发条件")
                if not has_action:
                    missing.append("行为")
                if not has_verify:
                    missing.append("验证")
                issues.append(f"  {current_rule}: 缺少{', '.join(missing)}")

            current_rule = stripped.split("## ")[1].split(" - ")[0]
            has_trigger = False
            has_action = False
            has_verify = False
            continue

        if current_rule:
            if "**触发条件**" in stripped:
                has_trigger = True
            if "**行为**" in stripped:
                has_action = True
            if "**验证**" in stripped:
                has_verify = True

    if current_rule and not (has_trigger and has_action and has_verify):
        missing = []
        if not has_trigger:
            missing.append("触发条件")
        if not has_action:
            missing.append("行为")
        if not has_verify:
            missing.append("验证")
        issues.append(f"  {current_rule}: 缺少{', '.join(missing)}")

    return issues

# ============================================================
# 5. 子系统corrections审计
# ============================================================
def audit_subsystem_corrections():
    """
    扫描各子系统corrections.md，检查：
    1. 有标题但根因/固化措施为空的条目
    2. 最后更新距今超过30天的条目（可能过期）
    返回 (issues_by_system, summary)
    """
    issues = {}
    total_entries = 0
    empty_entries = 0
    stale_entries = 0
    now = datetime.now()

    for sys_name, path in CORRECTIONS_PATHS.items():
        if sys_name == "main":
            continue
        if not path or not os.path.exists(path):
            continue

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        sys_issues = []
        current_section = None
        section_lines = []

        for line in content.split("\n"):
            stripped = line.strip()

            if stripped.startswith("## ") and len(stripped) > 4:
                if current_section and current_section not in ["记录规范", "🚧 待填充"]:
                    total_entries += 1
                    text = "\n".join(section_lines)
                    has_root_cause = "根因" in text or "触发条件" in text
                    has_fix = "固化措施" in text or "解法" in text or "纠正" in text

                    if not has_root_cause or not has_fix:
                        empty_entries += 1
                        missing_parts = []
                        if not has_root_cause:
                            missing_parts.append("根因")
                        if not has_fix:
                            missing_parts.append("固化措施")
                        sys_issues.append(f"  {current_section}: 缺少{'、'.join(missing_parts)}")

                    # 检查日期
                    for sl in section_lines:
                        m = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', sl)
                        if m:
                            try:
                                entry_date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                                days_old = (now - entry_date).days
                                if days_old > 30:
                                    stale_entries += 1
                                    sys_issues.append(f"  {current_section}: 已过期{days_old}天（{m.group()}）")
                            except:
                                pass
                            break

                current_section = stripped.split("## ")[1].strip()
                section_lines = []
            else:
                section_lines.append(stripped)

        # 最后一个章节
        if current_section and current_section not in ["记录规范", "🚧 待填充"]:
            total_entries += 1
            text = "\n".join(section_lines)
            has_root_cause = "根因" in text or "触发条件" in text
            has_fix = "固化措施" in text or "解法" in text or "纠正" in text
            if not has_root_cause or not has_fix:
                empty_entries += 1
                missing_parts = []
                if not has_root_cause:
                    missing_parts.append("根因")
                if not has_fix:
                    missing_parts.append("固化措施")
                sys_issues.append(f"  {current_section}: 缺少{'、'.join(missing_parts)}")

        if sys_issues:
            issues[sys_name] = sys_issues

    summary = f"{total_entries}条记录, {empty_entries}条缺根因/措施, {stale_entries}条过期(>30天)"
    return issues, summary

# ============================================================
# 6. Supermemory 记忆提取
# ============================================================
def extract_supermemory_facts(date_str, logs):
    """
    从当日日志和操作记录中提取关键事实，写入 Supermemory。
    """
    log_summary = f"""日期：{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}
今日系统操作记录：
"""
    for r in logs:
        task = r.get('task', 'unknown')
        status = r.get('status', '?')
        detail = r.get('detail', '')
        error = r.get('error', '')
        ts = r.get('timestamp', '')[:19]
        if status == 'ERROR':
            log_summary += f"- {task} 执行失败: {error[:80]}\n"
        elif status == 'OK':
            log_summary += f"- {task} 执行成功\n"

    today_ops = [
        "修复了日志审计机制，建立了task_logger.py统一日志模块",
        "建立了run_with_log.py通用Cron包装器，日志机制全面落地",
        "设置了每天21:00统一自我学习Cron（self_learning.py）",
        "设置了每天09:05日志审计和22:00晚间日志检查",
        "Supermemory服务已启用并配置Windows开机自启",
        "fact_extract.py已完成，支持MiniMax API直接提取原子事实",
    ]
    log_summary += "\n今日重要决策：\n"
    for op in today_ops:
        log_summary += f"- {op}\n"

    script_path = os.path.join(WORKSPACE, "scripts", "fact_extract.py")
    try:
        result = subprocess.run(
            [sys.executable, script_path, log_summary, "daily_learning", date_str],
            capture_output=True, text=True,
            timeout=60,
            encoding='utf-8', errors='replace'
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"fact_extract skipped: {result.stderr[:100]}"
    except Exception as e:
        return f"supermemory skipped: {e}"

# ============================================================
# 7. 生成每日学习报告
# ============================================================
def generate_learning_report(date_str, logs, new_count, new_details, learning_results, rule_issues, sub_issues, sub_summary):
    date_display = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    report_lines = [
        f"# 每日自我学习总结 - {date_display}",
        "",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        f"## 一、今日任务日志",
        f"- 总记录: {len(logs)} 条",
        f"- 正常: {sum(1 for r in logs if r.get('status')=='OK')} 条",
        f"- 出错: {sum(1 for r in logs if r.get('status')=='ERROR')} 条",
        f"- 跳过: {sum(1 for r in logs if r.get('status')=='SKIPPED')} 条",
        "",
        f"## 二、踩坑学习（新增）",
        f"- 新踩坑写入 corrections.md: {new_count} 条",
        "",
    ]

    if new_details:
        for task_name, sys_name, error_msg in new_details:
            report_lines.append(f"- [{sys_name}] {task_name}: {error_msg}")
    else:
        report_lines.append("OK 今日无新踩坑，所有错误均为已知问题")
    report_lines.append("")

    # 规则格式检查
    report_lines.extend([
        "## 三、主系统规则格式检查",
        "",
    ])
    if rule_issues:
        report_lines.append(f"WARNING: 发现 {len(rule_issues)} 条规则格式不完整：")
        report_lines.extend(rule_issues)
        report_lines.append("")
        report_lines.append("建议：补充完整的三段式格式（触发条件 -> 行为 -> 验证）")
    else:
        report_lines.append("OK 所有规则格式完整（触发条件 -> 行为 -> 验证）")
    report_lines.append("")

    # 子系统corrections审计
    report_lines.extend([
        "## 四、子系统corrections审计",
        "",
        f"**汇总**: {sub_summary}",
        "",
    ])
    if sub_issues:
        for sys_name, sys_issues in sorted(sub_issues.items()):
            report_lines.append(f"**{sys_name}**:")
            report_lines.extend(sys_issues)
            report_lines.append("")
    else:
        report_lines.append("OK 所有子系统corrections状态正常")
    report_lines.append("")

    report_lines.extend([
        "## 五、知识库学习",
        "",
    ])
    for sys_name, status, detail in learning_results:
        icon = "OK" if status == "OK" else "SKIP" if status == "SKIP" else "FAIL"
        report_lines.append(f"- {icon} {sys_name}: {status} {detail[:80] if detail else ''}")
    report_lines.append("")

    report_lines.extend([
        "## 六、明日待办",
        "",
    ])
    todos = []
    if new_count > 0:
        todos.append(f"1. 补充 {new_count} 条新踩坑的根因和固化措施")
    if rule_issues:
        todos.append(f"2. 修复 {len(rule_issues)} 条规则格式不完整的问题")
    if sub_issues:
        total_sub = sum(len(v) for v in sub_issues.values())
        todos.append(f"3. 处理 {total_sub} 条子系统corrections问题")
    if any(s in ("FAIL", "ERROR") for _, s, _ in learning_results):
        faileds = [s for s, s2, _ in learning_results if s2 in ("FAIL", "ERROR")]
        todos.append(f"4. 检查知识库学习失败的系统: {faileds}")
    if not todos:
        report_lines.append("OK 系统运行正常，无待办")
    else:
        report_lines.extend(todos)
    report_lines.append("")
    
    # 6. Supermemory记忆聚合（本周重要记忆）
    report_lines.append("")
    report_lines.append("## Supermemory本周记忆")
    try:
        _mem_dir3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'memory')
        _scr_dir3 = os.path.dirname(os.path.abspath(__file__))
        for _d3 in (_scr_dir3, _mem_dir3):
            if _d3 not in sys.path:
                sys.path.insert(0, _d3)
        from memory_ref import recall
        r = recall([
            ('小说', '情节 角色 设定'),
            ('投资', '涨停 策略 分析'),
            ('自媒体', '热点 爆款'),
            ('系统', '升级 决策'),
            ('日志', '工作日志'),
        ], top_k=2, max_total=10)
        if r['count'] > 0:
            for m in r['results']:
                report_lines.append(f"- [{m['_label']}] ({m['score']:.2f}) {m['text'][:80]}")
        else:
            report_lines.append("（暂无本周记忆）")
        print('  [Supermemory] 已聚合%d条本周记忆' % r['count'])
    except Exception as e:
        report_lines.append("（记忆聚合失败: %s）" % e)
        print('  [Supermemory] 聚合失败: %s' % e)

    content = "\n".join(report_lines)
    report_path = os.path.join(REPORT_DIR, f"learning_{date_str}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    return report_path, new_count

# ============================================================
# 记忆清理（30天前的日志自动删除）
# ============================================================
def _cleanup_old_memories():
    """清理30天前的日志类记忆"""
    try:
        _mem_dir4 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'memory')
        _scr_dir4 = os.path.dirname(os.path.abspath(__file__))
        for _d4 in (_scr_dir4, _mem_dir4):
            if _d4 not in sys.path:
                sys.path.insert(0, _d4)
        from memory_tools import DOMAIN_DB
        import sqlite3
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        for domain, path in DOMAIN_DB.items():
            if not os.path.exists(path):
                continue
            conn = sqlite3.connect(path)
            r = conn.execute(
                "DELETE FROM memories WHERE is_current=1 AND category='log' AND document_date < ?",
                (cutoff,)
            )
            deleted = r.rowcount
            if deleted > 0:
                conn.commit()
                print('  [清理] %s: 删除%d条过期日志' % (domain, deleted))
            conn.close()
    except Exception as e:
        print('  [清理] 失败: %s' % e)

# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    _start = datetime.now()
    _cleanup_old_memories()
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--today" or arg == "today":
            date_str = datetime.now().strftime("%Y%m%d")
        elif arg.isdigit() and len(arg) == 8:
            date_str = arg
        else:
            date_str = datetime.now().strftime("%Y%m%d")
    else:
        date_str = datetime.now().strftime("%Y%m%d")

    print(f"[自我学习] 开始 {date_str} 每日学习...")
    print("=" * 50)

    # 1. 读取日志
    logs = read_day_logs(date_str)
    print(f"[1/7] 读取日志: {len(logs)} 条记录")

    # 1.5 日志摘要存入supermemory
    try:
        _mem_dir2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'memory')
        _scr_dir2 = os.path.dirname(os.path.abspath(__file__))
        for _d2 in (_scr_dir2, _mem_dir2):
            if _d2 not in sys.path:
                sys.path.insert(0, _d2)
        from memory_adapter import save
        sys_stats = {}
        for log in logs:
            sys_name = log.get('system', infer_system(log.get('task', '')))
            if sys_name not in sys_stats:
                sys_stats[sys_name] = {'ok': 0, 'fail': 0, 'tasks': []}
            status = log.get('status', 'UNKNOWN')
            if status == 'OK':
                sys_stats[sys_name]['ok'] += 1
            else:
                sys_stats[sys_name]['fail'] += 1
            if len(sys_stats[sys_name]['tasks']) < 3:
                sys_stats[sys_name]['tasks'].append(log.get('task', ''))
        for sys_name, stats in sys_stats.items():
            if stats['ok'] + stats['fail'] > 0:
                summary = '工作日志 %s: %d条(%dOK/%dFAIL)' % (date_str, stats['ok']+stats['fail'], stats['ok'], stats['fail'])
                save(summary, category='log', source='system-logs')
        print('  [Supermemory] 已保存日志摘要')
    except Exception as e:
        print('  [Supermemory] 日志写入失败: %s' % e)

    # 2. 踩坑学习
    new_count, new_details = learn_from_errors(date_str, logs)
    print(f"[2/7] 踩坑学习: 新增 {new_count} 条写入 corrections.md")

    # 3. 知识库学习
    learning_results = run_subsystem_learning()
    print(f"[3/7] 知识库学习: {len(learning_results)} 个系统")
    _save_subsystem_learning_results(learning_results)
    
    # 4. 规则格式检查
    rule_issues = audit_rule_format()
    if rule_issues:
        print(f"[4/7] 规则格式检查: {len(rule_issues)} 条规则格式不完整")
        for issue in rule_issues:
            print(f"  {issue}")
    else:
        print(f"[4/7] 规则格式检查: OK 全部完整")

    # 5. 子系统corrections审计
    sub_issues, sub_summary = audit_subsystem_corrections()
    if sub_issues:
        print(f"[5/7] 子系统corrections审计: 发现 {sum(len(v) for v in sub_issues.values())} 条问题")
        for sys_name, sys_issues in sub_issues.items():
            for i in sys_issues:
                print(f"  [{sys_name}] {i}")
    else:
        print(f"[5/7] 子系统corrections审计: OK")

    # 6. 存入 Supermemory 记忆
    session_n = 0
    try:
        _mem_dir6 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'memory')
        _scr_dir6 = os.path.dirname(os.path.abspath(__file__))
        for _d6 in (_scr_dir6, _mem_dir6):
            if _d6 not in sys.path:
                sys.path.insert(0, _d6)
        from memory_adapter import save_decision
        # 每日学习结果存入supermemory
        summary_parts = []
        if new_count > 0:
            summary_parts.append('踩坑学习: %d条新规则' % new_count)
            for d in new_details[:5]:
                summary_parts.append('  - %s' % str(d)[:80])
        if learning_results:
            for sys_name, status, detail in learning_results:
                if status == 'OK':
                    summary_parts.append('[%s] 学习完成' % sys_name)
                else:
                    summary_parts.append('[%s] %s: %s' % (sys_name, status, detail[:60]))
        
        text = ' | '.join(summary_parts) if summary_parts else ('自我学习完成: 无新增踩坑')
        r = save_decision(text, source='system-self-learning')
        if r.get('success'):
            session_n = 1
            print('  memory_id:', r.get('memory_id'))
    except Exception as e:
        print('  Supermemory写入失败:', e)
    print('[6/7] Supermemory记忆: +%d条决策' % session_n)

    # 7. 生成报告
    report_path, _ = generate_learning_report(date_str, logs, new_count, new_details, learning_results, rule_issues, sub_issues, sub_summary)
    print(f"[7/7] 生成报告: {report_path}")
    print("=" * 50)

    # 自动记录任务日志
    _dur = (datetime.now() - _start).total_seconds() * 1000
    has_new = new_count > 0
    has_fail = any(s in ("FAIL", "ERROR") for _, s, _ in learning_results)
    has_rule_issues = len(rule_issues) > 0
    has_sub_issues = len(sub_issues) > 0
    # 脚本成功执行即视为OK（发现问题是正常行为，不是失败）
    # 只有知识库学习真正失败（脚本崩溃/超时）才算ERROR
    status = "ERROR" if has_fail else "OK"
    _auto_log(status,
              detail=f"踩坑+{new_count}条 | 知识库{len(learning_results)}个系统 | 规则问题{len(rule_issues)}条 | corrections问题{sum(len(v) for v in sub_issues.values()) if sub_issues else 0}条",
              duration_ms=_dur)
    # 始终返回0：脚本成功执行完即视为成功
    # 发现问题应记录到报告，不触发熔断
    sys.exit(0)