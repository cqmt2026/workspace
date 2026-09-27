# -*- coding: utf-8 -*-
"""扫描所有含截断腾讯Key的文件"""
import os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'.'
ELLIPSIS = '\u2026'

print("="*70)
print("【扫描含截断腾讯Key的文件】")
print("="*70)

# 搜索所有.py .json .md 文件中的截断Key
truncated_patterns = ['JGGBZ-…DFLJ', "JGGBZ-' + '…DFLJ", '…DFLJ']

found = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    # 跳过node_modules等目录
    if 'node_modules' in dirpath or '.git' in dirpath:
        continue
    for fname in filenames:
        if fname.endswith('.py') or fname.endswith('.json') or fname.endswith('.md'):
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if ELLIPSIS in content and ('JGGBZ' in content or 'TX_KEY' in content or '腾讯' in content):
                    found.append(fpath)
                    # 显示含截断Key的行
                    for i, line in enumerate(content.split('\n'), 1):
                        if ELLIPSIS in line and 'JGGBZ' in line:
                            print(f"\n  📄 {fpath}:{i}")
                            print(f"    {line.strip()[:100]}")
            except:
                pass

print(f"\n{'='*70}")
print(f"共找到 {len(found)} 个含截断Key的文件")
print("="*70)