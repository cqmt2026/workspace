import os
import glob
import re

scripts = []
scripts += glob.glob(r'C:\Users\Administrator\.openclaw\workspace\scripts\*.py')
scripts += glob.glob(r'C:\Users\Administrator\.openclaw\workspace\workspace-*/scripts/*.py')
scripts += glob.glob(r'C:\Users\Administrator\.openclaw\workspace\workspace-*/scripts/**/*.py', recursive=True)

fix_code = 'if sys.stdout is not None and hasattr(sys.stdout, \'buffer\') and sys.stdout.buffer is not None:\n    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=\'utf-8\', errors=\'replace\')\n'

fixed_count = 0
for s in scripts:
    try:
        with open(s, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'TextIOWrapper' in content:
            continue
        if '__main__' not in content or 'def main' not in content:
            continue
        if 'import io' not in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    lines.insert(i, 'import io')
                    break
            content = '\n'.join(lines)
        pattern = r'if __name__ == ["\']__main__["\']:'
        if re.search(pattern, content):
            content = re.sub(pattern, fix_code + '\n' + r'\g<0>', content)
            with open(s, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_count += 1
    except:
        pass
print(f'Fixed {fixed_count} Python scripts')