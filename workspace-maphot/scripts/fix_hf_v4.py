#!/usr/bin/env python3
import re

html_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 合并选择器后的逗号和换行
# tl.fromTo("sel", \n  { -> tl.fromTo("sel", {
content = re.sub(r'(tl\.\w+\("[^"]*"\),)\s*\n(\s+\{)', r'\1\n\2', content)
content = re.sub(r"(tl\.\w+\('[^']*'),)\s*\n(\s+\{)", r"\1\n\2", content)

errors_before = len(re.findall(r'tl\.\w+\("[^"]*",\s*\n\s+\{', content))
print(f"Remaining errors: {errors_before}")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
