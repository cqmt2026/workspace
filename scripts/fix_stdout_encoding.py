import os
import glob
import re

# Find all Python scripts
scripts = []
scripts += glob.glob(r'C:\Users\Administrator\.openclaw\workspace\scripts\*.py')
scripts += glob.glob(r'C:\Users\Administrator\.openclaw\workspace\workspace-*/scripts/*.py')
scripts += glob.glob(r'C:\Users\Administrator\.openclaw\workspace\workspace-*/scripts/**/*.py', recursive=True)

fix_code = '''if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
'''

fixed_count = 0
files_modified = []

for s in scripts:
    try:
        with open(s, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if needs fix
        if 'TextIOWrapper' in content:
            continue
        if '__main__' not in content:
            continue
        if 'def main' not in content:
            continue
            
        # Add import io if not present
        if 'import io' not in content:
            # Add after first import line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    lines.insert(i, 'import io')
                    break
            content = '\n'.join(lines)
        
        # Add fix before if __name__ == "__main__":
        pattern = r'if __name__ == ["\']__main____["\']:'
        if re.search(pattern, content):
            # Insert fix code before the if __name__ block
            content = re.sub(
                pattern,
                fix_code + '\n' + r'\g<0>',
                content
            )
            
            with open(s, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_count += 1
            files_modified.append(os.path.basename(s))
            
    except Exception as e:
        pass

print(f'Fixed {fixed_count} scripts')
for f in files_modified[:10]:
    print(f'  - {f}')
