#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P3 - 时效管理：过期知识自动降权/标记
规则：
1. 超过30天未修改的笔记标记为"低活跃"
2. 超过90天未修改的笔记标记为"可能过期"
3. 在 frontmatter 中添加 status 字段
4. 生成过期知识报告
"""

import os
import re
import sys
import datetime
import io

OBSIDIAN_VAULT = r"F:\Obsidian\Jarvis"
OUTPUT_DIR = r"C:\Users\Administrator\.openclaw\workspace\out_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 跳过这些分类的时效检查
SKIP_CLASSIFICATIONS = ["00-日记", "Z-归档"]


def check_and_update_notes():
    """检查所有笔记的时效性，更新 frontmatter"""
    now = datetime.datetime.now()
    low_active = []
    possibly_expired = []
    updated_count = 0

    for root, dirs, files in os.walk(OBSIDIAN_VAULT):
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, OBSIDIAN_VAULT)

            # 跳过特定分类
            skip = False
            for s in SKIP_CLASSIFICATIONS:
                if rel.startswith(s):
                    skip = True
                    break
            if skip:
                continue

            # 获取文件修改时间
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fp))
            days_old = (now - mtime).days

            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    content = fh.read()
            except:
                continue

            # 判断是否需要标记
            new_status = ""
            if days_old >= 90:
                new_status = "possibly_expired"
                possibly_expired.append((rel, days_old))
            elif days_old >= 30:
                new_status = "low_activity"
                low_active.append((rel, days_old))

            if not new_status:
                continue

            # 检查 frontmatter
            fm_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
            if fm_match:
                fm_text = fm_match.group(1)
                # 如果已有 status 字段且值相同，跳过
                if f"status: {new_status}" in fm_text:
                    continue
                # 替换或添加 status
                if "status:" in fm_text:
                    new_fm = re.sub(r"status:.*", f"status: {new_status}", fm_text)
                else:
                    new_fm = fm_text.rstrip() + f"\nstatus: {new_status}"
                new_content = content.replace(fm_text, new_fm, 1)
                with open(fp, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                updated_count += 1
            else:
                # 无 frontmatter，添加
                new_content = f"---\ncreated: \nsource: \nstatus: {new_status}\n---\n\n{content}"
                with open(fp, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                updated_count += 1

    return low_active, possibly_expired, updated_count


def generate_report(low_active, possibly_expired):
    """生成过期知识报告"""
    lines = []
    lines.append("# P3 时效管理报告")
    lines.append(f"> 生成时间: {datetime.datetime.now().isoformat()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if possibly_expired:
        lines.append(f"## 可能过期（≥90天未修改）: {len(possibly_expired)} 篇")
        for rel, days in sorted(possibly_expired, key=lambda x: -x[1]):
            lines.append(f"- [{rel}] ({days}天)")
        lines.append("")

    if low_active:
        lines.append(f"## 低活跃（30-89天未修改）: {len(low_active)} 篇")
        for rel, days in sorted(low_active, key=lambda x: -x[1]):
            lines.append(f"- [{rel}] ({days}天)")
        lines.append("")

    if not possibly_expired and not low_active:
        lines.append("## 所有笔记均为近期活跃状态")
        lines.append("")

    lines.append("---")
    lines.append("_由 P3 时效管理系统自动维护_")

    content = "\n".join(lines)
    outpath = os.path.join(OUTPUT_DIR, "p3_freshness_report.md")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(content)

    return outpath


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    low_active, possibly_expired, updated = check_and_update_notes()
    report_path = generate_report(low_active, possibly_expired)

    print(f"P3: 扫描完成")
    print(f"P3: 更新了 {updated} 篇笔记的 frontmatter status")
    print(f"P3: 低活跃(30-89天): {len(low_active)} 篇")
    print(f"P3: 可能过期(>=90天): {len(possibly_expired)} 篇")
    print(f"P3: 报告已生成: {report_path}")