import os
import re

obsidian = r'F:\Obsidian\Jarvis'
fixed_count = 0
files_modified = []

for root, dirs, files in os.walk(obsidian):
    for f in files:
        if f.endswith('.md'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                
                # Find all wikilinks with path prefix or .md extension
                def fix_wikilink(match):
                    full = match.group(0)
                    inner = match.group(1)
                    # Remove path prefix and .md extension
                    if '/' in inner:
                        inner = inner.split('/')[-1]
                    if inner.endswith('.md'):
                        inner = inner[:-3]
                    return f'[[{inner}]]'
                
                new_content = re.sub(r'\[\[([^\]]+)\]\]', fix_wikilink, content)
                
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as fp:
                        fp.write(new_content)
                    fixed_count += 1
                    rel_path = os.path.relpath(path, obsidian)
                    files_modified.append(rel_path)
                    
            except Exception as e:
                pass

print(f'Fixed {fixed_count} files')
for f in files_modified[:10]:
    print(f'  - {f}')
