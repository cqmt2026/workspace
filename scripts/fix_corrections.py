import os

# Fix corrections.md - remove duplicate R012
p = r'C:\Users\Administrator\.openclaw\workspace\corrections.md'
with open(p, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
new_lines = []
r012_seen = False
for line in lines:
    if line.startswith('## R012'):
        if not r012_seen:
            r012_seen = True
            new_lines.append(line)
        continue
    new_lines.append(line)

cleaned = '\n'.join(new_lines)
with open(p, 'w', encoding='utf-8') as f:
    f.write(cleaned)

print(f'Fixed corrections.md - R012 count now: {cleaned.count("## R012")}')

# Update trap manual
p2 = r'C:\Users\Administrator\.openclaw\workspace\shared-knowledge\系统知识图谱与常见陷阱手册.md'
with open(p2, 'r', encoding='utf-8') as f:
    content2 = f.read()

# Find the table section
table_start = content2.find('| 日期 | 陷阱 | 解决方案 |')
if table_start > 0:
    # Find the end of table (next ---)
    table_end = content2.find('\n---', table_start)
    if table_end > 0:
        # Insert before the ---
        new_entry = '\n| 2026-08-03 | 新增模型未加入白名单 | 配置新provider后必须在 agents.defaults.models 显式声明 |'
        content2 = content2[:table_end] + new_entry + content2[table_end:]
        with open(p2, 'w', encoding='utf-8') as f:
            f.write(content2)
        print('Updated trap manual')
    else:
        print('No table end found')
else:
    print('No table found in trap manual')
