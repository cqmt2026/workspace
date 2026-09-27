#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复HyperFrames HTML - 合并GSAP多行调用"""
import re

html_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复模式：选择器+逗号+换行+对象
# tl.fromTo("sel", \n  { vars }) -> tl.fromTo("sel", { vars })
pattern = r'(tl\.\w+\("[^"]*"),)\s*\n(\s+\{)'
fixed = re.sub(pattern, r'\1\n\2', content)

# 也处理单引号版本
pattern2 = r"(tl\.\w+\('[^']*'),)\s*\n(\s+\{)"
fixed = re.sub(pattern2, r"\1\n\2", fixed)

errors_before = len(re.findall(r'tl\.\w+\("[^"]*",\s*\n\s+\{', content))
errors_after = len(re.findall(r'tl\.\w+\("[^"]*",\s*\n\s+\{', fixed))
print(f"Errors before: {errors_before}")
print(f"Errors after: {errors_after}")

if fixed != content:
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(fixed)
    print("File updated")
else:
    print("No changes")
