#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import sys

html_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复双引号选择器
pattern1 = r'(tl\.\w+\("[^"]*"\),)\s*\n(\s+\{)'
content = re.sub(pattern1, r'\1\n\2', content)

# 修复单引号选择器（使用不同分隔符）
pattern2 = "(tl\\.\\w+\\('[^']*'),)\\s*\\n(\\s+\\{)"
content = re.sub(pattern2, r'\1\n\2', content)

errors_before = len(re.findall(r'tl\.\w+\("[^"]*",\s*\n\s+\{', content))
print(f"Errors after fix: {errors_before}")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed")
