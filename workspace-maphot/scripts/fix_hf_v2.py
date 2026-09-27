#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复HyperFrames HTML - 将多行GSAP调用改为单行"""
import re

html_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复模式：tl.fromTo("selector", \n  { vars }, position);
# 改为：tl.fromTo("selector", { vars }, position);
# 只处理选择器+对象的模式（不包含onUpdate等复杂情况）

lines = content.split('\n')
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # 检查是否是tl.to(或tl.fromTo(开头
    stripped = line.strip()
    if stripped.startswith('tl.to(') or stripped.startswith('tl.fromTo('):
        # 收集完整的调用
        full_call = line
        j = i + 1
        while j < len(lines):
            next_line = lines[j].strip()
            full_call += '\n' + lines[j]
            # 检查是否闭合（有分号或右括号后跟逗号+位置）
            if next_line.endswith(');') or (next_line.startswith('}, T') and next_line.endswith(');')):
                break
            j += 1
        
        # 尝试修复：移除选择器后的逗号和换行
        # 模式: tl.fromTo("sel", \n  { ... })
        # 改为: tl.fromTo("sel", { ... })
        fixed = re.sub(r'(tl\.\w+\("([^"]+)"\),)\s*\n(\s+\{)', r'\1\n\3', full_call)
        fixed = re.sub(r"(tl\.\w+\('([^']+)'", r"\1'", fixed)  # 单引号版本
        
        # 如果修复成功（行数减少），使用修复后的
        if fixed.count('\n') < full_call.count('\n'):
            fixed_lines.append(fixed)
            i = j + 1
            continue
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)
    
    i += 1

fixed_content = '\n'.join(fixed_lines)

# 验证修复效果
errors_before = len(re.findall(r'tl\.\w+\(".*?",\s*\n\s+\{', content))
errors_after = len(re.findall(r'tl\.\w+\(".*?",\s*\n\s+\{', fixed_content))
print(f"Syntax errors before: {errors_before}")
print(f"Syntax errors after: {errors_after}")

if fixed_content != content:
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    print("File updated successfully")
else:
    print("No changes made")
