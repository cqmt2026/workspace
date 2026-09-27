# -*- coding: utf-8 -*-
"""系统全面检查脚本 - 13维度"""
import os, sys, glob, re, subprocess, datetime

WS = r"C:\Users\Administrator\.openclaw\workspace"
OUT = []

def log(msg):
    print(msg)
    OUT.append(msg)

# ==================== ① 安全策略 ====================
log("=" * 60)
log("① 安全策略检查")
log("=" * 60)

# 密钥硬编码扫描
KEY_PAT = re.compile(r'(api[_-]?key|apikey|secret|passwd|password|client_secret|access_token|MX_APIKEY)\s*[:=]\s*["\']?[^"\'\s]{8,}', re.I)
KEY_LONG = re.compile(r'(sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16,})')
EXCLUDE = ["node_modules", ".git", "backup", ".venv", "site-packages", "__pycache__", "vendor"]
SKIP_EXT = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mp3", ".wav", ".zip", ".exe", ".dll", ".pdf"}

secrets = []
files_scanned = 0
for root, dirs, files in os.walk(WS):
    dirs[:] = [d for d in dirs if d not in EXCLUDE]
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in SKIP_EXT or ext not in (".py", ".js", ".json", ".txt", ".md", ".sh", ".toml", ".ini", ".cfg", ".env"):
            continue
        p = os.path.join(root, f)
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
            files_scanned += 1
            for m in KEY_PAT.finditer(content):
                line_start = content.rfind("\n", 0, m.start()) + 1
                line = content[m.start():][:80].replace("\n", " ")
                secrets.append((os.path.relpath(p, WS), m.group(1), line))
        except:
            pass

log(f"扫描文件数: {files_scanned}")
log(f"命中密钥模式: {len(secrets)}")
seen = set()
for p, k, line in secrets[:10]:
    key = (p, k)
    if key in seen:
        continue
    seen.add(key)
    log(f"  - {p} | {k} | {line[:60]}")

# 敏感文件暴露
log("\n敏感文件检查:")
sensitive = [".env", ".env.local", "secrets.json", "credentials.json", "id_rsa", "token.json"]
for root, dirs, files in os.walk(WS):
    for f in files:
        if f in sensitive:
            log(f"  [!] 暴露: {os.path.relpath(os.path.join(root,f), WS)}")

# Git忽略规则
gitignore = os.path.join(WS, ".gitignore")
if os.path.exists(gitignore):
    with open(gitignore, "r", encoding="utf-8") as f:
        glines = f.readlines()
    log(f"\n.gitignore: OK ({len(glines)} 行)")
    for pat in ["*.env", "secrets", "*.key", "id_rsa"]:
        found = any(pat in l for l in glines)
        log(f"  {pat}: {'OK' if found else '[!] 未忽略'}")
else:
    log("\n.gitignore: [!] 不存在")

# ==================== ② 运行状态 ====================
log("\n" + "=" * 60)
log("② 运行状态检查")
log("=" * 60)

# Cron任务（Windows schtasks）
log("\nCron任务状态:")
try:
    r = subprocess.run(["schtasks", "/query", "/fo", "list", "/v"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = r.stdout
    oc_count = sum(1 for l in lines.split("\n") if "openclaw" in l.lower() or "OpenClaw" in l)
    log(f"  OpenClaw相关任务: {oc_count}")
except Exception as e:
    log(f"  [!] schtasks查询失败: {e}")

# 脚本语法检查
log("\n核心脚本语法检查:")
core_scripts = [
    "scripts/pipeline.py",
    "scripts/选题采集_v3.py",
    "scripts/脚本生成_v3.py",
    "scripts/地图绘制_v5.py",
    "scripts/配音生成_v2.py",
    "scripts/视频合成_v2.py",
    "scripts/发布推送.py",
    "scripts/hyperframes_template.py",
    "scripts/config_loader.py",
    "scripts/cn_io.py",
    "scripts/humanize_text.py",
    "scripts/obsidian_sync.py",
    "scripts/obsidian_audit.py",
    "scripts/obsidian_daily.py",
    "scripts/obsidian_save.py",
    "scripts/obsidian_correct.py",
    "scripts/obsidian_link.py",
]
errors = []
for script in core_scripts:
    p = os.path.join(WS, script)
    if not os.path.exists(p):
        errors.append(f"  [!] 不存在: {script}")
        continue
    r = subprocess.run(["python", "-m", "py_compile", p], capture_output=True, text=True)
    if r.returncode == 0:
        log(f"  OK: {script}")
    else:
        errors.append(f"  [!] {script}: {r.stderr[:100]}")
        log(f"  FAIL: {script}")
if errors:
    log("\n错误汇总:")
    for e in errors:
        log(e)

# ==================== ③ 文档一致性 ====================
log("\n" + "=" * 60)
log("③ 文档一致性检查")
log("=" * 60)

core_files = ["SOUL.md", "MEMORY.md", "AGENTS.md", "USER.md", "IDENTITY.md", "TOOLS.md", "HEARTBEAT.md", "coding-standards.md"]
log("\n核心8文件:")
for f in core_files:
    p = os.path.join(WS, f)
    exists = os.path.exists(p)
    size = os.path.getsize(p) if exists else 0
    log(f"  {'OK' if exists else '[!]'} {f} ({size}B)")

# TOOLS.md引用检查
log("\nTOOLS.md脚本引用:")
tools_md = os.path.join(WS, "TOOLS.md")
if os.path.exists(tools_md):
    with open(tools_md, "r", encoding="utf-8") as f:
        tcontent = f.read()
    scripts = re.findall(r"`scripts/[^`]+\.py`", tcontent)
    for s in scripts:
        fname = s.replace("`", "").replace("scripts/", "")
        p = os.path.join(WS, "scripts", fname)
        exists = os.path.exists(p)
        log(f"  {'OK' if exists else '[!]'} {fname}")

# 日期更新检查
log("\n文档更新日期:")
for fname in core_files:
    p = os.path.join(WS, fname)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        matches = re.findall(r"最后更新[：:]\s*(\d{4}-\d{2}-\d{2})", content)
        if matches:
            last = matches[-1]
            days = (datetime.date.today() - datetime.date.fromisoformat(last)).days
            status = "OK" if days <= 30 else "[!]"
            log(f"  {status} {fname}: {last} ({days}天前)")
        else:
            log(f"  [!] {fname}: 无更新日期")

# ==================== ④ 文件结构 ====================
log("\n" + "=" * 60)
log("④ 文件结构检查")
log("=" * 60)

# 废弃脚本
log("\n废弃脚本 (test_/debug_/verify_/_*check*):")
patterns = ["test_*.py", "debug_*.py", "verify_*.py", "*_check*.py"]
for pat in patterns:
    matches = glob.glob(os.path.join(WS, "**", pat), recursive=True)
    for m in matches:
        rel = os.path.relpath(m, WS)
        log(f"  [!] {rel}")

# 空目录
log("\n空目录:")
empty_dirs = []
for root, dirs, files in os.walk(WS):
    if not dirs and not files:
        empty_dirs.append(root.replace(WS, "."))
log(f"  空目录数: {len(empty_dirs)}")
for d in empty_dirs[:5]:
    log(f"    {d}")

# 超大文件
log("\n超大文件 (>50MB):")
big = []
for root, dirs, files in os.walk(WS):
    dirs[:] = [d for d in dirs if d not in ["node_modules", ".git", ".venv", "__pycache__", "cache"]]
    for f in files:
        p = os.path.join(root, f)
        try:
            sz = os.path.getsize(p)
            if sz > 50 * 1024 * 1024:
                big.append((os.path.relpath(p, WS), sz // 1024 // 1024))
        except:
            pass
for b in sorted(big, key=lambda x: -x[1])[:10]:
    log(f"  [!] {b[0]} ({b[1]}MB)")
log(f"  超大文件数: {len(big)}")

# ==================== ⑤ 记忆系统 ====================
log("\n" + "=" * 60)
log("⑤ 记忆系统检查")
log("=" * 60)

# Supermemory分库
log("\nSupermemory分库:")
for name in ["bank", "knowledge", "shared-knowledge"]:
    p = os.path.join(WS, name)
    if os.path.exists(p):
        count = sum(len(f) for _, _, f in os.walk(p))
        log(f"  OK {name}: {count} files")
    else:
        log(f"  [!] {name}: 不存在")

# 修复日志
fix_dir = os.path.join(WS, "memory", "日志", "修复日志")
if os.path.exists(fix_dir):
    logs = glob.glob(os.path.join(fix_dir, "fix_*.md"))
    log(f"\n修复日志: {len(logs)} 条")
    this_month = [l for l in logs if "202608" in l]
    last_month = [l for l in logs if "202607" in l]
    log(f"  本月(8月): {len(this_month)} 条")
    log(f"  上月(7月): {len(last_month)} 条")
    for log_f in sorted(logs)[-5:]:
        log(f"    {os.path.basename(log_f)}")
else:
    log("\n[!] 修复日志目录不存在")

# 系统知识手册
hk = os.path.join(WS, "shared-knowledge", "系统知识图谱与常见陷阱手册.md")
if os.path.exists(hk):
    sz = os.path.getsize(hk)
    with open(hk, "r", encoding="utf-8") as f:
        hcontent = f.read()
    log(f"\n系统知识手册: OK ({sz//1024}KB, {len(hcontent.splitlines())}行)")
else:
    log("\n[!] 系统知识手册不存在")

# ==================== ⑥ 子系统深度 ====================
log("\n" + "=" * 60)
log("⑥ 子系统深度检查")
log("=" * 60)

subsystems = {
    "投资": ["workspace-investment"],
    "小说": ["workspace-novel"],
    "自媒体": ["workspace-social"],
    "数学动画": ["workspace-math"],
    "微信小程序": ["workspace-weixin"],
    "地图热点": ["workspace-maphot"],
    "百都": ["workspace-baiduagent"],
}
for name, dirs in subsystems.items():
    for d in dirs:
        p = os.path.join(WS, d)
        if os.path.exists(p):
            count = sum(len(f) for _, _, f in os.walk(p))
            log(f"\n{name} ({d}): OK ({count} files)")
            # 关键文件
            if name == "投资":
                scripts = glob.glob(os.path.join(p, "scripts", "*.py"))
                models = glob.glob(os.path.join(p, "**", "*.pkl"), recursive=True)
                log(f"  脚本: {len(scripts)}, ML模型: {len(models)}")
            elif name == "小说":
                chapters = glob.glob(os.path.join(p, "data", "chapters", "*.txt"))
                log(f"  章节: {len(chapters)} 章")
                if chapters:
                    latest = max(os.path.getmtime(c) for c in chapters)
                    log(f"  最新章节: {datetime.datetime.fromtimestamp(latest)}")
            elif name == "自媒体":
                outputs = glob.glob(os.path.join(p, "output", "**", "*"), recursive=True)
                log(f"  输出: {len(outputs)} 文件")
            elif name == "数学动画":
                videos = glob.glob(os.path.join(p, "output", "*.mp4"))
                log(f"  视频: {len(videos)} 个")
                # Manim检查
                r = subprocess.run(["manim", "--version"], capture_output=True, text=True)
                log(f"  Manim: {'OK' if r.returncode == 0 else '[!]'} {r.stdout.strip()[:50] if r.stdout else ''}")
            elif name == "微信小程序":
                wx_scripts = glob.glob(os.path.join(p, "**", "*.py"), recursive=True)
                corr = glob.glob(os.path.join(p, "**", "corrections*"), recursive=True)
                log(f"  脚本: {len(wx_scripts)}, corrections: {len(corr)}")
            elif name == "地图热点":
                maphot_videos = glob.glob(os.path.join(p, "output", "**", "*.mp4"), recursive=True)
                log(f"  视频: {len(maphot_videos)} 个")
                # pipeline检查
                pipeline = os.path.join(p, "scripts", "core", "pipeline.py")
                log(f"  pipeline.py: {'OK' if os.path.exists(pipeline) else '[!]'}")
            elif name == "百都":
                canvas = os.path.join(p, "canvas", "index.html")
                log(f"  Canvas看板: {'OK' if os.path.exists(canvas) else '[!]'}")
        else:
            log(f"\n[!] {name} ({d}): 不存在")

# Obsidian
obs = r"F:\Obsidian\Jarvis"
if os.path.exists(obs):
    count = sum(len(f) for _, _, f in os.walk(obs))
    log(f"\nObsidian库: OK ({count} 文件)")
else:
    log(f"\n[!] Obsidian库不存在: {obs}")

# ==================== ⑦ 技能与工具 ====================
log("\n" + "=" * 60)
log("⑦ 技能与工具检查")
log("=" * 60)

# Skills
skill_dirs = glob.glob(os.path.join(WS, "..", "..", "..", "AppData", "Roaming", "npm", "node_modules", "openclaw", "skills", "*"))
agent_skills = glob.glob(os.path.join(WS, "..", "..", "..", ".agents", "skills", "*"))
all_skills = []
for d in skill_dirs:
    if os.path.isdir(d):
        name = os.path.basename(d)
        skill_md = os.path.join(d, "SKILL.md")
        all_skills.append((name, os.path.exists(skill_md)))
for d in agent_skills:
    if os.path.isdir(d):
        name = os.path.basename(d)
        skill_md = os.path.join(d, "SKILL.md")
        all_skills.append((name, os.path.exists(skill_md)))

log(f"\n总Skill数: {len(all_skills)}")
missing = [s for s, e in all_skills if not e]
log(f"缺SKILL.md: {len(missing)} → {missing[:5]}")
log(f"OK: {len(all_skills) - len(missing)}")

# 关键工具
log("\n关键工具:")
tools = [
    ("Python", ["python", "--version"]),
    ("FFmpeg", ["ffmpeg", "-version"]),
    ("Node", ["node", "--version"]),
    ("npx", ["npx", "--version"]),
]
for name, cmd in tools:
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout.strip().split("\n")[0][:50]
    log(f"  {'OK' if r.returncode == 0 else '[!]'} {name}: {out}")

# Playwright
r = subprocess.run(["python", "-c", "import playwright; print(playwright.__version__)"], capture_output=True, text=True)
log(f"  {'OK' if r.returncode == 0 else '[!]'} Playwright: {r.stdout.strip()[:50] if r.stdout else ''}")

# ==================== ⑧ 编程能力 ====================
log("\n" + "=" * 60)
log("⑧ 编程能力检查")
log("=" * 60)

# 修复日志趋势
fix_dir = os.path.join(WS, "memory", "日志", "修复日志")
if os.path.exists(fix_dir):
    logs = sorted(glob.glob(os.path.join(fix_dir, "fix_*.md")))
    this_month = [l for l in logs if "202608" in l]
    last_month = [l for l in logs if "202607" in l]
    log(f"\n修复日志趋势:")
    log(f"  本月(8月): {len(this_month)} 条")
    log(f"  上月(7月): {len(last_month)} 条")
    log(f"  总计: {len(logs)} 条")
    # 检查是否有重复错误
    error_patterns = {}
    for log_f in logs:
        with open(log_f, "r", encoding="utf-8") as f:
            content = f.read()
        # 提取错误类型
        for line in content.split("\n"):
            if "陷阱" in line or "错误" in line or "bug" in line.lower():
                error_patterns[line[:50]] = error_patterns.get(line[:50], 0) + 1
    duplicates = [k for k, v in error_patterns.items() if v > 1]
    if duplicates:
        log(f"  [!] 重复错误模式: {len(duplicates)} 个")
    else:
        log(f"  OK: 无重复错误")

# ==================== ⑨ 汇报产出 ====================
log("\n" + "=" * 60)
log("⑨ 汇报产出检查")
log("=" * 60)

log_dirs = ["memory/日志/系统检查", "memory/日志/修复日志", "memory/日志/session"]
for d in log_dirs:
    p = os.path.join(WS, d)
    if os.path.exists(p):
        count = len(glob.glob(os.path.join(p, "*")))
        log(f"  OK {d}: {count} 文件")
    else:
        log(f"  [!] {d}: 不存在")

# 系统检查历史
check_dir = os.path.join(WS, "memory", "日志", "系统检查")
if os.path.exists(check_dir):
    checks = sorted(glob.glob(os.path.join(check_dir, "*.md")))
    log(f"\n历史检查: {len(checks)} 份")
    for c in checks[-5:]:
        log(f"  {os.path.basename(c)}")

# ==================== ⑩ 商业化进展 ====================
log("\n" + "=" * 60)
log("⑩ 商业化进展")
log("=" * 60)

# 番茄小说
novel_chapters = glob.glob(os.path.join(WS, "workspace-novel", "data", "chapters", "*.txt"))
log(f"\n小说章节: {len(novel_chapters)} 章")

# 自媒体
social_out = os.path.join(WS, "workspace-social", "output")
if os.path.exists(social_out):
    posts = glob.glob(os.path.join(social_out, "**", "*.md"), recursive=True)
    log(f"自媒体内容: {len(posts)} 篇")

# 地图热点
maphot_out = os.path.join(WS, "workspace-maphot", "output")
if os.path.exists(maphot_out):
    videos = glob.glob(os.path.join(maphot_out, "**", "*.mp4"), recursive=True)
    log(f"地图热点视频: {len(videos)} 个")

# PPT模板
ppt_out = os.path.join(WS, "scripts", "output", "ppt_templates_v3")
if os.path.exists(ppt_out):
    ppt_files = glob.glob(os.path.join(ppt_out, "*.pptx"))
    log(f"PPT模板: {len(ppt_files)} 套")

# 数学动画
math_out = os.path.join(WS, "workspace-math", "output")
if os.path.exists(math_out):
    vids = glob.glob(os.path.join(math_out, "*.mp4"))
    log(f"数学动画视频: {len(vids)} 个")

# 投资
inv_data = os.path.join(WS, "workspace-investment", "data")
if os.path.exists(inv_data):
    reports = glob.glob(os.path.join(inv_data, "*report*")) + glob.glob(os.path.join(inv_data, "*分析*"))
    log(f"投资报告: {len(reports)} 份")

# ==================== ⑪ 外部依赖 ====================
log("\n" + "=" * 60)
log("⑪ 外部依赖健康度")
log("=" * 60)

# 检查.env
env_file = os.path.join(WS, ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        content = f.read()
    keys = ["MX_APIKEY", "WECHAT_TOKEN", "BING_API", "GATEWAY"]
    for k in keys:
        if k in content:
            log(f"  {k}: OK")
        else:
            log(f"  {k}: [!] 未配置")
else:
    log("\n[!] .env文件不存在")

# Gateway状态
log("\nGateway状态:")
try:
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://127.0.0.1:18789/health"], capture_output=True, text=True)
    if r.stdout == "200":
        log("  Gateway: OK (运行中)")
    else:
        log(f"  Gateway: [!] HTTP {r.stdout}")
except Exception as e:
    log(f"  Gateway: [!] 连接失败: {e}")

# ==================== ⑫ 系统学习 ====================
log("\n" + "=" * 60)
log("⑫ 系统学习与成长")
log("=" * 60)

# 修复日志趋势（已在⑧检查）
# 知识沉淀
obs = r"F:\Obsidian\Jarvis"
if os.path.exists(obs):
    # 检查最近7天的日记
    week_ago = datetime.date.today() - datetime.timedelta(days=7)
    daily_count = 0
    for d in glob.glob(os.path.join(obs, "00-日记", "*.md")):
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(d)).date()
        if mtime >= week_ago:
            daily_count += 1
    log(f"\n最近7天日记: {daily_count} 篇")
    # 检查审计日志
    audit = os.path.join(obs, "审计报告.md")
    if os.path.exists(audit):
        with open(audit, "r", encoding="utf-8") as f:
            acontent = f.read()
        log(f"审计报告: OK ({len(acontent)} 字符)")
    else:
        log("审计报告: [!] 不存在")

# ==================== ⑬ 备份与恢复 ====================
log("\n" + "=" * 60)
log("⑬ 备份与恢复")
log("=" * 60)

backup_dir = os.path.join(WS, "memory", "备份")
if os.path.exists(backup_dir):
    sessions = glob.glob(os.path.join(backup_dir, "session_*"))
    systems = glob.glob(os.path.join(backup_dir, "system_*"))
    log(f"\nSession备份: {len(sessions)}")
    log(f"系统备份: {len(systems)}")
    all_backups = sessions + systems
    if all_backups:
        latest = max(os.path.getmtime(b) for b in all_backups)
        dt = datetime.datetime.fromtimestamp(latest)
        log(f"最新备份: {dt}")
        # 检查有效期
        days_old = (datetime.datetime.now() - dt).days
        if days_old > 90:
            log(f"  [!] 备份已过时 ({days_old}天)")
        else:
            log(f"  OK: 备份新鲜 ({days_old}天前)")
else:
    log("\n[!] 备份目录不存在")

# ==================== 汇总 ====================
log("\n" + "=" * 60)
log("汇总")
log("=" * 60)
log(f"检查时间: {datetime.datetime.now()}")
log(f"总发现: {len(secrets)} 个密钥风险, {len(empty_dirs)} 个空目录, {len(big)} 个超大文件")
log("检查完成")

# 保存报告
report_dir = os.path.join(WS, "memory", "日志", "系统检查")
os.makedirs(report_dir, exist_ok=True)
report_file = os.path.join(report_dir, f"系统检查_{datetime.date.today().isoformat()}.md")
with open(report_file, "w", encoding="utf-8") as f:
    f.write("\n".join(OUT))
log(f"\n报告已保存: {report_file}")
