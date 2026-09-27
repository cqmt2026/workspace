#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess, sys, os, json, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

OUT_DIR = r'C:\Users\Administrator\.openclaw\workspace\out_data'
MX_DATA_PY = r'C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\skills\mx-data\mx_data.py'

results = {}

queries = [
    ('商业航天板块 今日行情', 'mx_data_board.txt'),
    ('航天ETF 159267 今日行情', 'mx_data_etf159267.txt'),
    ('航空航天ETF华夏 159227 今日', 'mx_data_etf159227.txt'),
    ('军工板块 今日行情', 'mx_data_jungong.txt'),
    ('中航沈飞 600760 今日行情', 'mx_data_shenfei.txt'),
    ('航发动力 600893 今日行情', 'mx_data_hdongli.txt'),
    ('西部超导 688122 今日行情', 'mx_data_xibu.txt'),
]

for q, fname in queries:
    try:
        cmd = [sys.executable, MX_DATA_PY, q, OUT_DIR]
        r = subprocess.run(cmd, capture_output=True, timeout=30, encoding='utf-8', errors='replace')
        out = r.stdout[:3000]
        results[fname] = out
        print(f"[OK] {q}")
    except Exception as e:
        results[fname] = str(e)
        print(f"[FAIL] {q}: {e}")

# Write all results
for fname, content in results.items():
    fpath = os.path.join(OUT_DIR, fname)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

print("All results written to out_data")
