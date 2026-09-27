# -*- coding: utf-8 -*-
"""检查所有脚本中使用的腾讯Key"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

files = {
    'fetch_tencent_poi.py': 'scripts/modules/fetch_tencent_poi.py',
    'fetch_tencent_complete.py': 'scripts/modules/fetch_tencent_complete.py',
    'tencent_quota_check.py': 'scripts/core/tencent_quota_check.py',
    'tencent_key_verify.py': 'scripts/core/tencent_key_verify.py',
    'tencent_diagnosis.py': 'scripts/core/tencent_diagnosis.py',
    'debug_tencent_zero.py': 'scripts/debug_tencent_zero.py',
    'test_tencent_full.py': 'scripts/modules/test_tencent_full.py',
}

print("="*60)
print("【所有脚本中的腾讯Key检查】")
print("="*60)

ELLIPSIS = '\u2026'  # … 

for name, path in files.items():
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 查找 TX_KEY 或 key 赋值
        key_match = re.search(r"(?:TX_KEY|KEY)\s*=\s*['\"]([^'\"]+)['\"]", content)
        if key_match:
            key = key_match.group(1)
            has_ellipsis = ELLIPSIS in key
            has_dots = '...' in key
            print(f"\n{name}:")
            print(f"   Key = {key}")
            print(f"   长度 = {len(key)} 字符")
            print(f"   含省略号(…): {has_ellipsis}")
            print(f"   含3点(...): {has_dots}")
            print(f"   ⚠️ 截断Key!" if has_ellipsis or has_dots else "   ✅ 完整Key")
        else:
            print(f"\n{name}: 未找到Key")
    except Exception as e:
        print(f"\n{name}: ❌ 无法读取: {e}")

print("\n" + "="*60)
print("【结论】")
print("="*60)