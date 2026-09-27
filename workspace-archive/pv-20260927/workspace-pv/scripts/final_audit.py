# -*- coding: utf-8 -*-
import json, os, sys, re
from pathlib import Path

BASE = Path(__file__).parent.parent
output_dir = BASE / "data" / "output" / "llm_generated"

with open(output_dir / "llm_generated_20260820.json", "r", encoding="utf-8") as f:
    contents = json.load(f)

passed = []
needs_fix = []

for c in contents:
    issues = []
    text = c["hook"] + c["body"] + c["cta"]

    if any(x in text for x in ["测试", "占位符", "{title", "{kw}"]):
        issues.append("含占位符")

    has_num = bool(re.search(r'\d+', c["hook"]))
    has_q = bool(re.search(r'[？?！!]', c["hook"]))
    if not (has_num or has_q):
        issues.append("钩子缺数字/问句")

    if len(c["body"]) < 100:
        issues.append(f"正文太短({len(c['body'])}字)")

    if "私信" not in c["cta"] and "关注" not in c["cta"]:
        issues.append("CTA无明确行动")

    if issues:
        needs_fix.append({"title": c["title"][:40], "issues": issues})
    else:
        passed.append(c)

print(f"AUDIT: {len(contents)} total | {len(passed)} passed | {len(needs_fix)} need fix")
for nf in needs_fix:
    print(f"  FIX: {nf['title']}... | {nf['issues']}")

# 统计方向分布
dir_count = {}
for c in contents:
    d = c["direction"]
    dir_count[d] = dir_count.get(d, 0) + 1
print(f"DIRECTION: {json.dumps(dir_count, ensure_ascii=False)}")
print(f"PASS RATE: {len(passed)/len(contents)*100:.0f}%")
