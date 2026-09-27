#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描所有脚本中的地图API Key"""
import os
import re

found_keys = set()

# 检查已知脚本
known_scripts = [
    'scripts/core/tencent_key_verify.py',
    'scripts/core/check_tx_keys.py',
    'scripts/modules/fetch_amap_around.py',
    'scripts/modules/fetch_amap_around_v2.py',
    'scripts/modules/fetch_jxzb_fix.py',
    'scripts/modules/fetch_poi_batch.py',
    'scripts/modules/fetch_second_tier.py',
    'scripts/modules/fetch_sp_special.py',
    'scripts/modules/fetch_tier2_expand.py',
    'scripts/modules/fetch_tier2_from_sp.py',
    'scripts/modules/fetch_tier2_full.py',
    'scripts/modules/fetch_tier2_v3.py',
    'scripts/modules/fetch_tier2_v4.py',
]

for script in known_scripts:
    if os.path.exists(script):
        content = open(script, encoding='utf-8').read()
        # 查找类似 JGGBZ-xxxxx-xxxxx 的腾讯Key格式
        tx_matches = re.findall(r"['\"][A-Za-z0-9]{7}-[A-Za-z0-9]{7}-[A-Za-z0-9]{7}['\"]", content)
        for m in tx_matches:
            found_keys.add(m.strip('\"\''))
        # 查找高德Key格式
        amap_matches = re.findall(r"['\"][A-Za-z0-9]{32}['\"]", content)
        for m in amap_matches:
            val = m.strip('\"\'')
            if len(val) == 32 and val != 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0':
                found_keys.add(val)

# 也扫描所有py文件
for root, dirs, files in os.walk('scripts'):
    for fn in files:
        if fn.endswith('.py'):
            fp = os.path.join(root, fn)
            if fp in known_scripts:
                continue
            try:
                content = open(fp, encoding='utf-8').read()
                # 腾讯Key
                tx = re.findall(r"['\"][A-Za-z0-9]{7}-[A-Za-z0-9]{7}-[A-Za-z0-9]{7}['\"]", content)
                for m in tx:
                    found_keys.add(m.strip('\"\''))
            except:
                pass

print(f"找到的Key: {found_keys}")
