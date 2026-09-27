# -*- coding: utf-8 -*-
"""审核重新生成的内容质量"""
import sys, os, json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

def safe_print(msg):
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            print(msg)
    except: pass

REWRITTEN_DIR = BASE / "data" / "output" / "rewritten"
output_dir = BASE / "data" / "output"
output_dir.mkdir(exist_ok=True)

# 读取JSON
json_file = REWRITTEN_DIR / "rewritten_20260820.json"
if not json_file.exists():
    safe_print("未找到生成结果")
    sys.exit(1)

with open(json_file, "r", encoding="utf-8") as f:
    contents = json.load(f)

safe_print(f"审核 {len(contents)} 条重新生成的内容\n")

# 逐条审核
passed = []
needs_fix = []

for c in contents:
    issues = []
    checks = []

    # 检查1: 无测试/占位符
    text = c["hook"] + c["body"] + c["cta"]
    if "测试" in text or "占位符" in text or "{title" in text:
        issues.append("含测试/占位符")
    checks.append(("无占位符", not any(x in text for x in ["测试", "占位符", "{title"])))

    # 检查2: 钩子有数字/问句
    has_number = bool(__import__('re').search(r'\d+', c["hook"]))
    has_question = bool(__import__('re').search(r'[？?！!]', c["hook"]))
    if not (has_number or has_question):
        issues.append("钩子缺数字/问句")
    checks.append(("钩子有数字/问句", has_number or has_question))

    # 检查3: 正文有具体内容（不只是框架）
    body_lines = [l.strip() for l in c["body"].split("\n") if l.strip()]
    info_lines = [l for l in body_lines if len(l) > 10]
    if len(info_lines) < 3:
        issues.append("正文内容太短")
    checks.append(("正文有实质内容", len(info_lines) >= 3))

    # 检查4: CTA有明确行动
    if "私信" in c["cta"] or "评论" in c["cta"]:
        checks.append(("CTA有明确行动", True))
    else:
        issues.append("CTA无明确行动")
        checks.append(("CTA有明确行动", False))

    if issues:
        needs_fix.append({"title": c["title"][:40], "issues": issues})
    else:
        passed.append(c)

    safe_print(f"[{'✅' if not issues else '⚠️'}] {c['title'][:40]}...")
    if issues:
        for iss in issues:
            safe_print(f"    问题: {iss}")

safe_print(f"\n{'='*50}")
safe_print(f"审核结果: {len(passed)}/{len(contents)} 条通过")
if needs_fix:
    safe_print(f"需修复: {len(needs_fix)} 条")
    for nf in needs_fix:
        safe_print(f"  ⚠️ {nf['title']}...")
        for iss in nf['issues']:
            safe_print(f"     - {iss}")
else:
    safe_print("全部通过！内容质量达标。")

# 保存报告
report = {
    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "total": len(contents),
    "passed": len(passed),
    "failed": len(needs_fix),
    "details": [{"title": c["title"][:50], "direction": c["direction"], "hook": c["hook"][:40]} for c in contents],
}
report_file = output_dir / "rewrite_audit_20260820.txt"
report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
safe_print(f"\n报告: {report_file}")
