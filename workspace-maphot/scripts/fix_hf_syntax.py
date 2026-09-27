#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复HyperFrames HTML中的GSAP语法错误"""
import re

html_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

original = content

# 修复1: 选择器字符串后跟逗号+换行+对象的模式
# 错误: tl.to(".selector', \n  { props })
# 正确: tl.to(".selector', { props })
pattern1 = r'(tl\.\w+\()(["\'])([^"\']*)\2\s*,\s*\n(\s+\{)'
content = re.sub(pattern1, r'\1\2\3\2,\n\4', content)

# 修复2: 处理动态拼接的选择器
# 错误: tl.to('.dof-blur[data-depth=''"'"" + 1 + '"'"'], \n  { "--dof": ...
# 正确: tl.to('.dof-blur[data-depth=''"'"" + 1 + '"'"'), { "--dof": ...
pattern2 = r"(tl\.\w+\()('(?:[^'\\]|\\.)*')\s*,\s*\n(\s+\{)"
content = re.sub(pattern2, r"\1\2',\n\3", content)

# 修复3: 删除空的script标签
content = re.sub(r'<script></script>\s*', '', content)

# 修复4: 恢复audio标签（取消注释）
content = content.replace('<!-- <audio id="audio" src="assets/audio.mp3" data-start="0" data-track-index="0"></audio> -->', 
                          '<audio id="audio" src="assets/audio.mp3" data-start="0" data-track-index="0"></audio>')

if content != original:
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed! Changes made.")
else:
    print("No changes needed.")

# 验证修复
print("\nVerification:")
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if 'tl.to(' in line or 'tl.fromTo(' in line:
        stripped = line.strip()
        if stripped.endswith(','):
            next_line = lines[i].strip() if i < len(lines) else ''
            if next_line.startswith('{'):
                print(f"  Line {i}: Still has comma issue")
                print(f"    {stripped[:60]}")
