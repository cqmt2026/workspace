#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可悦 -> Obsidian 知识库审计 + 可信度评估
每周日20:00执行
"""

import os
import sys
import datetime
import re
import io

OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"
REPORT_FILE = os.path.join(OBSIDIAN_VAULT, "Z-归档", "知识库检查报告.md")

# 来源可信度映射
SOURCE_CREDIBILITY = {
    "auto_init": {"label": "系统文档", "score": "高", "icon": "✅"},
    "manual_save": {"label": "主人提供", "score": "高", "icon": "✅"},
    "auto_collect": {"label": "模型生成", "score": "中", "icon": "⚠️"},
    "unknown": {"label": "未知来源", "score": "低", "icon": "❓"},
}


def check_all():
    now = datetime.datetime.now()
    today = now.date()
    cutoff_30d = today - datetime.timedelta(days=30)

    issues = []
    stats = {"总笔记": 0, "各分类": {}, "可信度统计": {"高": 0, "中": 0, "低": 0}}
    credibility_details = []

    for root, dirs, files in os.walk(OBSIDIAN_VAULT):
        if ".obsidian" in root or ".git" in root:
            continue

        md_files = [f for f in files if f.endswith(".md")]
        if not md_files:
            continue

        rel_path = os.path.relpath(root, OBSIDIAN_VAULT)
        count = len(md_files)
        stats["总笔记"] += count
        stats["各分类"][rel_path] = count

        for f in md_files:
            filepath = os.path.join(root, f)
            mtime = os.path.getmtime(filepath)
            mtime_date = datetime.datetime.fromtimestamp(mtime).date()

            try:
                with open(filepath, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except Exception as e:
                issues.append("❌ 无法读取: " + filepath + " (" + str(e) + ")")
                continue

            # 解析frontmatter
            source = "unknown"
            corrected = False
            correction_note = ""

            fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if fm_match:
                fm_text = fm_match.group(1)
                s_match = re.search(r'^source:\s*(.+)$', fm_text, re.MULTILINE)
                if s_match:
                    source = s_match.group(1).strip()
                c_match = re.search(r'^corrected:\s*(true|yes)$', fm_text, re.MULTILINE)
                if c_match:
                    corrected = True
                cn_match = re.search(r'^correction_note:\s*(.+)$', fm_text, re.MULTILINE)
                if cn_match:
                    correction_note = cn_match.group(1).strip()
            else:
                issues.append("⚠️ 缺少frontmatter: " + filepath)

            # 可信度评估
            cred = SOURCE_CREDIBILITY.get(source, SOURCE_CREDIBILITY["unknown"])
            stats["可信度统计"][cred["score"]] += 1
            credibility_details.append({
                "path": filepath,
                "source": source,
                "credibility": cred["score"],
                "corrected": corrected,
                "correction_note": correction_note,
            })

            # 检查内容过短
            if len(content.strip()) < 50:
                issues.append("⚠️ 内容过短(<50字): " + filepath)

            # 检查30天未更新
            if mtime_date < cutoff_30d:
                days_old = (today - mtime_date).days
                issues.append("⏰ " + str(days_old) + "天未更新: " + filepath)

    return issues, stats, credibility_details


def write_report(issues, stats, credibility_details):
    today = datetime.date.today().isoformat()
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

    md = "# 知识库检查报告\n\n"
    md += "检查日期: " + today + "\n\n"
    md += "---\n\n"

    # 统计
    md += "## 📊 知识库概况\n\n"
    md += "| 指标 | 数值 |\n"
    md += "|------|------|\n"
    md += "| 总笔记数 | " + str(stats["总笔记"]) + " |\n"
    md += "| 分类数 | " + str(len(stats["各分类"])) + " |\n\n"

    # 可信度概览
    md += "## ✅ 可信度评估\n\n"
    md += "| 等级 | 数量 | 含义 |\n"
    md += "|------|------|------|\n"
    for score in ["高", "中", "低"]:
        count = stats["可信度统计"][score]
        meaning = {"高": "系统文档/主人提供，可信", "中": "模型生成，需交叉验证", "低": "未知来源，谨慎使用"}
        md += "| " + score + " | " + str(count) + " | " + meaning[score] + " |\n"

    md += "\n### 可信度分布图\n"
    total = max(stats["总笔记"], 1)
    for score in ["高", "中", "低"]:
        count = stats["可信度统计"][score]
        bar = "█" * int(count / total * 30) if total > 0 else ""
        pct = round(count / total * 100)
        md += "- " + score + ": " + bar + " " + str(count) + " (" + str(pct) + "%)\n"

    md += "\n### 勘误笔记\n\n"
    corrected_notes = [c for c in credibility_details if c["corrected"]]
    if corrected_notes:
        md += "共 " + str(len(corrected_notes)) + " 篇已标记勘误：\n\n"
        for c in corrected_notes:
            rel = os.path.relpath(c["path"], OBSIDIAN_VAULT)
            note = c.get("correction_note", "无说明")
            md += "- [[" + rel.replace("\\", "/").replace(".md", "") + "]]: " + note + "\n"
    else:
        md += "✅ 暂无勘误标记\n"
    md += "\n"

    md += "### 低可信度笔记\n\n"
    low_cred = [c for c in credibility_details if c["credibility"] == "低"]
    if low_cred:
        md += "共 " + str(len(low_cred)) + " 篇，建议核实来源：\n\n"
        for c in low_cred[:10]:
            rel = os.path.relpath(c["path"], OBSIDIAN_VAULT)
            md += "- [[" + rel.replace("\\", "/").replace(".md", "") + "]]\n"
        if len(low_cred) > 10:
            md += "- ...及其他 " + str(len(low_cred) - 10) + " 篇\n"
    else:
        md += "✅ 无低可信度笔记\n"
    md += "\n"

    # 各分类详情
    md += "### 各分类笔记数\n\n"
    md += "| 分类 | 笔记数 |\n"
    md += "|------|-------|\n"
    for path, count in sorted(stats["各分类"].items(), key=lambda x: -x[1]):
        md += "| " + path + " | " + str(count) + " |\n"

    md += "\n---\n\n"

    # 问题
    md += "## ⚠️ 发现的问题\n\n"
    if not issues:
        md += "✅ 未发现问题，知识库状态健康\n\n"
    else:
        md += "共发现 " + str(len(issues)) + " 个问题：\n\n"
        for issue in issues:
            md += "- " + issue + "\n"
        md += "\n"

    md += "---\n"
    md += "_由 可悦🌸 自动检查_\n"

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(md)

    return REPORT_FILE


def main():
    print("可悦知识库审计 + 可信度评估 - " + datetime.datetime.now().isoformat())
    print("Obsidian库: " + OBSIDIAN_VAULT)
    print()

    issues, stats, credibility = check_all()

    print("总笔记: " + str(stats["总笔记"]))
    print("可信度: 高" + str(stats["可信度统计"]["高"]) + " 中" + str(stats["可信度统计"]["中"]) + " 低" + str(stats["可信度统计"]["低"]))
    print("勘误数: " + str(len([c for c in credibility if c["corrected"]])))
    print("问题数: " + str(len(issues)))

    report = write_report(issues, stats, credibility)
    print()
    print("报告已保存: " + report)
    print("审计完成")


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()