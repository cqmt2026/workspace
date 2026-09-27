# -*- coding: utf-8 -*-
"""光伏内容质量评估工具 v0.1
逐条审核199条内容，输出A/B/C分级报告
"""
import os, sys, re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
CONTENT_DIR = BASE / "data" / "content"
OUTPUT_DIR = BASE / "data" / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# === 质量问题检测规则 ===

PASS_FAIL_PATTERNS = [
    ("测试政策", "C级-废弃", "含'测试'占位符，内容不真实"),
    ("示例", "C级-废弃", "含'示例'占位符"),
    ("占位符", "C级-废弃", "含'占位符'"),
    ("{title", "C级-废弃", "模板占位符未替换"),
    ("{kw}", "C级-废弃", "模板占位符未替换"),
    ("{price}", "C级-废弃", "模板占位符未替换"),
    ("{total}", "C级-废弃", "模板占位符未替换"),
    ("{days}", "C级-废弃", "模板占位符未替换"),
    ("{power}", "C级-废弃", "模板占位符未替换"),
    ("{kwh}", "C级-废弃", "模板占位符未替换"),
    ("{years}", "C级-废弃", "模板占位符未替换"),
    ("{N}", "C级-废弃", "模板占位符未替换"),
]

DUMMY_BODY_PATTERNS = [
    ("今天聊一个光伏人基本都遇到过的问题", "B级-改写", "正文以空洞钩子开头，无实际信息"),
    ("今天光伏圈最值得关注的就是", "B级-改写", "正文以空洞钩子开头"),
    ("不讲复杂术语，用大白话给你讲明白原理", "B级-改写", "正文只有模板框架，无具体解释"),
    ("这件事背后，是行业格局的深层变化", "B级-改写", "正文只有框架，无具体解读"),
    ("根据最新政策", "B级-改写", "政策解读正文过于笼统"),
]

WEAK_CTA_PATTERNS = [
    ("评论区留言你的问题", "B级-改写", "CTA过于泛泛，无明确价值承诺"),
    ("关注不迷路", "B级-改写", "CTA无行动引导，只是求关注"),
    ("评论区留言", "B级-改写", "CTA无明确价值锚点"),
    ("想了解更多", "B级-改写", "CTA无具体诱饵"),
]

STRONG_CTA_PATTERNS = [
    ("私信我", "A级候选", "CTA有明确行动指引"),
    ("免费帮你测算", "A级候选", "CTA有价值承诺"),
    ("私信获取", "A级候选", "CTA有价值交换"),
]


def analyze_content(text, filename):
    """分析单条内容质量"""
    issues = []
    positives = []
    
    # 1. 检查C级红线
    for pattern, verdict, reason in PASS_FAIL_PATTERNS:
        if pattern in text:
            issues.append((verdict, reason))
    
    # 2. 检查B级-改写
    for pattern, verdict, reason in DUMMY_BODY_PATTERNS:
        if pattern in text:
            issues.append((verdict, reason))
    
    # 3. 检查CTA质量
    for pattern, verdict, reason in WEAK_CTA_PATTERNS:
        if pattern in text:
            issues.append((verdict, reason))
    
    # 4. 检查CTA亮点
    for pattern, verdict, reason in STRONG_CTA_PATTERNS:
        if pattern in text:
            positives.append((verdict, reason))
    
    # 5. 检查标题钩子质量
    # 找第一行或包含【钩子】的行
    hook_line = ""
    for line in text.split("\n"):
        if "钩子" in line or line.startswith("【") or line.startswith("#"):
            hook_line = line
            break
        if "钩子:" in line:
            # 取冒号后的内容
            parts = line.split("钩子:", 1)
            if len(parts) > 1:
                hook_line = parts[1].strip()
                break
    
    # 钩子质量评估
    hook_quality = []
    has_number = bool(re.search(r'\d+', hook_line))
    has_question = bool(re.search(r'[？?！!]', hook_line))
    has_conflict = any(w in hook_line for w in ["但", "却", "别", "死", "结束", "变了"])
    has_benefit = any(w in hook_line for w in ["赚", "省", "收益", "划算", "回报"])
    has_curiosity = any(w in hook_line for w in ["不知道", "没想到", "竟然", "秘密", "真相"])
    
    hook_score = sum([has_number, has_question, has_conflict, has_benefit, has_curiosity])
    if hook_score >= 3:
        hook_quality.append("A")
    elif hook_score >= 2:
        hook_quality.append("B")
    else:
        hook_quality.append("C")
    
    # 6. 检查信息密度
    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("#") and not l.startswith("---")]
    info_lines = [l for l in lines if len(l) > 15]
    density = len(info_lines) / max(len(lines), 1)
    
    # 综合分级
    if issues:
        # 有硬伤→先看最严重的问题
        has_c = any("C级" in i[0] for i in issues)
        has_b = any("B级" in i[0] for i in issues)
        if has_c:
            final_grade = "C-废弃"
            reason = "含模板占位符/测试数据，必须重写"
        else:
            final_grade = "B-改写"
            reason = "; ".join(set(i[1] for i in issues))
    else:
        # 无硬伤，看软质量
        if hook_quality[0] == "A" and density > 0.5:
            final_grade = "A-可直接发布"
            reason = f"钩子强({hook_score}/5) + 信息密度{density:.0%}"
        elif hook_quality[0] == "B":
            final_grade = "B-改写"
            reason = f"钩子较弱({hook_score}/5)，需增强吸引力"
        else:
            final_grade = "B-改写"
            reason = f"信息密度偏低({density:.0%})，需补充具体内容"
    
    return {
        "filename": filename,
        "grade": final_grade,
        "reason": reason,
        "issues": issues,
        "positives": positives,
        "hook_quality": hook_quality[0],
        "hook_score": hook_score,
        "density": density,
        "total_lines": len(lines),
        "info_lines": len(info_lines),
    }


def audit_all():
    """审核所有已生成内容"""
    results = []
    files = sorted(CONTENT_DIR.glob("*.txt"))
    
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        result = analyze_content(text, f.name)
        results.append(result)
    
    # 统计
    grade_counts = {}
    for r in results:
        g = r["grade"]
        grade_counts[g] = grade_counts.get(g, 0) + 1
    
    # 生成报告
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append(f"光伏内容质量审核报告")
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append(f"审核文件数: {len(results)}")
    report_lines.append("=" * 60)
    report_lines.append("")
    report_lines.append("【分级统计】")
    for g, c in sorted(grade_counts.items(), key=lambda x: (x[0] != "A-可直接发布", x[0])):
        report_lines.append(f"  {g}: {c}条")
    report_lines.append("")
    
    report_lines.append("【A级 - 可直接发布】")
    a_items = [r for r in results if r["grade"] == "A-可直接发布"]
    if a_items:
        for r in a_items:
            report_lines.append(f"  ✅ {r['filename']}")
            report_lines.append(f"     {r['reason']}")
    else:
        report_lines.append("  (无)")
    report_lines.append("")
    
    report_lines.append("【B级 - 需改写】")
    b_items = [r for r in results if r["grade"] == "B-改写"]
    if b_items:
        for r in b_items:
            report_lines.append(f"  ⚠️  {r['filename']}")
            report_lines.append(f"     {r['reason']}")
    else:
        report_lines.append("  (无)")
    report_lines.append("")
    
    report_lines.append("【C级 - 直接废弃】")
    c_items = [r for r in results if r["grade"] == "C-废弃"]
    if c_items:
        for r in c_items:
            report_lines.append(f"  ❌ {r['filename']}")
            report_lines.append(f"     {r['reason']}")
    else:
        report_lines.append("  (无)")
    
    report_text = "\n".join(report_lines)
    
    # 保存
    today = datetime.now().strftime("%Y%m%d")
    report_file = OUTPUT_DIR / f"quality_audit_{today}.txt"
    report_file.write_text(report_text, encoding="utf-8")
    
    # 详细JSON（供后续改写用）
    import json
    json_file = OUTPUT_DIR / f"quality_audit_{today}.json"
    json_data = []
    for r in results:
        json_data.append({
            "filename": r["filename"],
            "grade": r["grade"],
            "reason": r["reason"],
            "hook_quality": r["hook_quality"],
            "hook_score": r["hook_score"],
            "density": round(r["density"], 2),
            "issues": [(i[0], i[1]) for i in r["issues"]],
        })
    json_file.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(report_text)
    print(f"\n报告已保存: {report_file}")
    print(f"详细数据: {json_file}")
    return results


if __name__ == "__main__":
    audit_all()
