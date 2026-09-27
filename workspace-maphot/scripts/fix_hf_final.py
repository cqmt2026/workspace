#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复HyperFrames GSAP语法错误"""
import re

html_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 检查原始错误数
original_errors = len(re.findall(r'tl\.\w+\("[^"]*",\)\s*\n\s+\{', content))
print(f"Original errors: {original_errors}")

# 修复模式：选择器后跟逗号+换行+对象
# tl.fromTo("sel", \n  { vars }, pos); -> tl.fromTo("sel", { vars }, pos);
pattern = r'(tl\.\w+\("[^"]*"\),)\s*\n(\s+\{)'
fixed = re.sub(pattern, r'\1\n\2', content)

# 也处理单引号版本
pattern2 = r"(tl\.\w+\('[^']*'),)\s*\n(\s+\{)"
fixed = re.sub(pattern2, r"\1\n\2", fixed)

# 检查修复后错误数
new_errors = len(re.findall(r'tl\.\w+\("[^"]*",\)\s*\n\s+\{', fixed))
print(f"After fix: {new_errors}")

# 恢复audio标签
fixed = fixed.replace('<!-- <audio id="audio"', '<audio id="audio"')
fixed = fixed.replace('data-track-index="0"></audio> -->', 'data-track-index="0"></audio>')

if fixed != content:
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(fixed)
    print("File updated")
else:
    print("No changes needed")

# 验证关键部分
print("\nVerification:")
lines = fixed.split('\n')
for i, line in enumerate(lines[820:850], 821):
    if 'tl.' in line:
        print(f"Line {i}: {line.strip()[:70]}")
