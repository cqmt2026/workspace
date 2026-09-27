#!/usr/bin/env python3
import re

html_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 检查错误数
errors = len(re.findall(r'tl\.\w+\("[^"]*",\)\s*\n\s+\{', content))
print(f"语法错误数: {errors}")

# 修复双引号选择器
pattern = r'(tl\.\w+\("[^"]*"\),)\s*\n(\s+\{)'
fixed = re.sub(pattern, r'\1\n\2', content)

# 恢复audio标签（取消注释）
fixed = fixed.replace('<!-- <audio id="audio"', '<audio id="audio"')
fixed = fixed.replace('data-track-index="0"></audio> -->', 'data-track-index="0"></audio>')

new_errors = len(re.findall(r'tl\.\w+\("[^"]*",\)\s*\n\s+\{', fixed))
print(f"修复后错误数: {new_errors}")

if fixed != content:
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(fixed)
    print("文件已更新")
    
    # 显示修复后的代码
    lines = fixed.split('\n')
    print("\n修复后的关键代码:")
    for i, line in enumerate(lines[820:840], 821):
        if 'tl.' in line:
            print(f"  Line {i}: {line.strip()[:80]}")
else:
    print("无需修改")
