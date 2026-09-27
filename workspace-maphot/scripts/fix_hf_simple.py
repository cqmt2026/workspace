#!/usr/bin/env python3
import re

html_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 只修复双引号版本（避免正则问题）
pattern = r'(tl\.\w+\("[^"]*"\),)\s*\n(\s+\{)'
fixed = re.sub(pattern, r'\1\n\2', content)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(fixed)

print("Fixed double-quote selectors")
