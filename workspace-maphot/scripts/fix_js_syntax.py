#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 HyperFrames HTML 中的 JavaScript 语法错误"""
import re

html_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复1: 删除空的script标签
content = re.sub(r'<script></script>\s*', '', content)

# 修复2: 选择器字符串后的逗号+换行问题
# 错误: tl.to(".dof-blur[data-depth='" + 1 + "'], \n  { "--dof": ...
# 正确: tl.to(".dof-blur[data-depth='" + 1 + "']", { "--dof": ...
# 匹配模式：选择器字符串末尾有逗号，下一行开始是对象
def fix_selector_comma(match):
    prefix = match.group(1)  # tl.to( 或 tl.fromTo(
    selector = match.group(2)  # 选择器内容（不含末尾引号）
    suffix = match.group(4)  # 后面的内容
    # 移除选择器后的逗号
    return prefix + selector + '",\n' + suffix

# 匹配 tl.to("selector', \n  { 模式
pattern = r'(tl\.\w+\()("(?:[^"\\]|\\.)*")\s*,\s*\n(\s+\{)'
content = re.sub(pattern, r'\1\2,\n\3', content)

# 也匹配单引号版本
pattern2 = r"(tl\.\w+\()('(?:[^'\\]|\\.)*')\s*,\s*\n(\s+\{)"
content = re.sub(pattern2, r"\1\2,\n\3", content)

# 修复3: 检查字符串拼接后的选择器
# 如: ".dof-blur[data-depth='" + 1 + "'], \n  {
pattern3 = r"""(tl\.\w+\()"([^"]*['\"]\s*\+\s*\d+\s*\+\s*['\"])",\s*\n(\s+\{)"""
content = re.sub(pattern3, r'\1\2",\n\3', content)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed JavaScript syntax errors in index.html")
