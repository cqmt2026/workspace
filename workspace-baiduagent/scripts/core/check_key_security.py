# -*- coding: utf-8 -*-
"""扫描所有含明文腾讯Key的脚本"""
import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'.'
TX_KEY_PATTERN = re.compile(r"TX_KEY\s*=\s*['\"]([A-Za-z0-9\-]+)['\"]")

print("="*70)
print("【腾讯Key明文使用检查】")
print("="*70)

found_issues = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    if 'node_modules' in dirpath or '.git' in dirpath:
        continue
    for fname in filenames:
        if fname.endswith('.py'):
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 查找包含TX_KEY赋值且值以JGGBZ开头的行
                for i, line in enumerate(content.split('\n'), 1):
                    if 'TX_KEY' in line and 'JGGBZ' in line:
                        # 排除环境变量读取方式
                        if 'os.environ' not in line and 'os.getenv' not in line:
                            found_issues.append({
                                'file': fpath,
                                'line': i,
                                'content': line.strip()
                            })
            except:
                pass

if found_issues:
    print(f"\n发现 {len(found_issues)} 处明文Key使用：")
    for issue in found_issues:
        print(f"\n  📄 {issue['file']}:{issue['line']}")
        print(f"     {issue['content'][:60]}...")
else:
    print("\n✅ 未发现明文Key使用")

print("\n" + "="*70)