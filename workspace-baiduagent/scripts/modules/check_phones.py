# -*- coding: utf-8 -*-
"""检查CSV中电话号码清洗情况"""
import csv, re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('data/master/kq_list_chongqing_latest.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    bad = 0
    total = 0
    samples = []
    for row in reader:
        total += 1
        p = row.get('电话', '')
        if ';' in p:
            parts = p.split(';')
            nums = []
            for part in parts:
                m = re.search(r'(1[3-9]\d{9}|023-?\d{7,8})', part.strip())
                if m:
                    nums.append(m.group(1).replace('-', ''))
            if len(nums) > 1:
                bad += 1
                if bad <= 5:
                    name = row.get('机构名称', '')
                    samples.append((name, p, ';'.join(nums)))
    print(f"Total rows: {total}")
    print(f"Multi-phone entries: {bad}")
    for s in samples:
        print(f"  Name: {s[0]}")
        print(f"    Raw:  {s[1]}")
        print(f"    Clean:{s[2]}")
        print()
