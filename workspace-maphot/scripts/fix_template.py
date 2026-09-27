# -*- coding: utf-8 -*-
"""Fix hyperframes_template.py JS brace escaping issue"""
import sys, re
sys.path.insert(0, 'scripts')
from core import hyperframes_template

format_placeholders = {'WIDTH','HEIGHT','TOTAL','city','year','total_gdp','gdp_rank',
    'TOTAL_GDP_RAW','INTRO_END','DISTRICT_ANIMATIONS','OUTRO_START','OUTRO_ID',
    'LAST_DISTRICT_ID','DISTRICT_SCENES','first','last','opt_a','opt_b','opt_c'}

html = hyperframes_template.HTML_MAIN

def escape_js_braces(text):
    tokens = {}
    positions = []
    for m in re.finditer(r'\{(\w+)\}', text):
        placeholder = '{' + m.group(1) + '}'
        if m.group(1) in format_placeholders:
            token = f'__FMT_{len(tokens)}__'
            tokens[token] = placeholder
            positions.append((m.start(), m.end(), token))
    result = text
    for start, end, token in reversed(positions):
        result = result[:start] + token + result[end:]
    in_script = False
    lines = result.split('\n')
    for i, line in enumerate(lines):
        if '<script' in line: in_script = True
        if '</script>' in line: in_script = False
        if in_script:
            line = line.replace('{', '{{').replace('}', '}}')
            lines[i] = line
    result = '\n'.join(lines)
    for token, placeholder in tokens.items():
        result = result.replace(token, placeholder)
    return result

escaped = escape_js_braces(html)

with open('scripts/core/hyperframes_template.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_start = content.index("HTML_MAIN = r'''")
search_marker = "\n\n# 每个区的场景HTML模板"
old_end = content.index(search_marker, old_start)
new_section = "HTML_MAIN = r'''" + escaped + "'''" + search_marker
new_content = content[:old_start] + new_section + content[old_end + len(search_marker):]

with open('scripts/core/hyperframes_template.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Fixed! New HTML_MAIN length:', len(escaped))

# Verify
import importlib
importlib.reload(hyperframes_template)
test = hyperframes_template.HTML_MAIN.format(
    WIDTH=1080, HEIGHT=1920, TOTAL=60, city='test', year='2026',
    total_gdp='3T', gdp_rank='1', TOTAL_GDP_RAW=3000,
    INTRO_END=7.5, DISTRICT_ANIMATIONS='', OUTRO_START=70,
    OUTRO_ID='outro', LAST_DISTRICT_ID='d10', DISTRICT_SCENES='',
    first='a', last='b', opt_a='x', opt_b='y', opt_c='z'
)
print('Format OK! Length:', len(test))
