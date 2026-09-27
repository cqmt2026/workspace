# -*- coding: utf-8 -*-
"""修复hyperframes_template.py中的JavaScript引号问题"""
import re

with open('scripts/core/hyperframes_template.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并修复data-depth的引号问题
# 原代码: tl.to(".dof-blur[data-depth='" + {depth} + "'],
# 应改为: tl.to('.dof-blur[data-depth="' + {depth} + '"],
content = content.replace(
    'tl.to(".dof-blur[data-depth=\'" + {depth} + "\'],',
    'tl.to(\'.dof-blur[data-depth="\' + {depth} + \'"]\','
)

content = content.replace(
    'tl.to(".dof-blur[data-depth=\'" + (dofTarget{did.upper()} + 1) + "\'],',
    'tl.to(\'.dof-blur[data-depth="\' + (dofTarget{did.upper()} + 1) + \'"]\','
)

content = content.replace(
    'tl.to(".dof-blur[data-depth=\'" + (dofTarget{did.upper()} + 2) + "\'],',
    'tl.to(\'.dof-blur[data-depth="\' + (dofTarget{did.upper()} + 2) + \'"]\','
)

content = content.replace(
    'tl.to(".dof-blur[data-depth=\'" + (dofTarget{did.upper()} + 3) + "\'],',
    'tl.to(\'.dof-blur[data-depth="\' + (dofTarget{did.upper()} + 3) + \'"]\','
)

with open('scripts/core/hyperframes_template.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed template')
