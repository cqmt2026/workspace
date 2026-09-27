#!/usr/bin/env python3
"""
因子IC历史分析 + 筛选有效因子
"""
import sqlite3, json, sys
from datetime import datetime, timedelta

DB = r'F:\market_data.db'
FACTOR_DB = r'data/factors.db'
OUT = r'out_data'

conn = sqlite3.connect(FACTOR_DB)

# 1. factor_status表
print("=== factor_status ===")
try:
    rows = conn.execute("SELECT * FROM factor_status ORDER BY name").fetchall()
    cols = [c[1] for c in conn.execute("PRAGMA table_info(factor_status)").fetchall()]
    print(f"  columns: {cols}")
    print(f"  rows: {len(rows)}")
    for r in rows:
        print(f"    {dict(zip(cols, r))}")
except Exception as e:
    print(f"  no factor_status table: {e}")

# 2. IC历史
print("\n=== IC历史 ===")
try:
    rows = conn.execute("SELECT date, factor, ic, p_value, sample_count FROM factor_ic ORDER BY date DESC LIMIT 50").fetchall()
    print(f"  {len(rows)} IC records")
    # 按因子分组
    from collections import defaultdict
    by_factor = defaultdict(list)
    for r in rows:
        by_factor[r[1]].append(r)
    for factor, records in sorted(by_factor.items()):
        dates = [r[0] for r in records]
        ics = [r[2] for r in records]
        avg_ic = sum(ics) / len(ics)
        pos_pct = sum(1 for i in ics if i > 0) / len(ics) * 100
        print(f"  {factor:20s} avg_IC={avg_ic:+.4f}  pos%={pos_pct:.0f}%  ({len(records)} days)")
except Exception as e:
    print(f"  no factor_ic table: {e}")

# 3. factors表结构
print("\n=== factors表结构 ===")
try:
    cols = conn.execute("PRAGMA table_info(factors)").fetchall()
    print(f"  columns: {[(c[1],c[2]) for c in cols]}")
    count = conn.execute("SELECT COUNT(*) FROM factors").fetchone()[0]
    print(f"  total rows: {count}")
    # 最新日期
    if any(c[1] == 'date' for c in cols):
        latest = conn.execute("SELECT MAX(date) FROM factors").fetchone()[0]
        print(f"  latest date: {latest}")
    # 按因子分组的行数
    factor_cols = [c[1] for c in cols if c[1] not in ('code', 'date', 'id')]
    print(f"  factor columns ({len(factor_cols)}): {factor_cols}")
    # 每个因子的非空比例
    for fc in factor_cols[:10]:
        nonnull = conn.execute(f"SELECT COUNT(*) FROM factors WHERE {fc} IS NOT NULL AND {fc} != 0").fetchone()[0]
        print(f"    {fc}: {nonnull}/{count} non-null")
except Exception as e:
    print(f"  factors table: {e}")

conn.close()

# 4. 检查ML训练管线
print("\n=== ML训练管线 ===")
import os
ml_dir = r'quant_ml\pipeline'
if os.path.exists(ml_dir):
    scripts = os.listdir(ml_dir)
    print(f"  {ml_dir} files: {scripts}")
    # 看unified_train.py参数
    train_script = os.path.join(ml_dir, 'unified_train.py')
    if os.path.exists(train_script):
        with open(train_script) as f:
            content = f.read()
        # 找参数解析部分
        if 'argparse' in content:
            import re
            args = re.findall(r"add_argument\('--(\w+)", content)
            print(f"  unified_train.py args: {args}")
        else:
            print(f"  unified_train.py: {len(content)} bytes (no argparse)")
else:
    print(f"  {ml_dir} not found!")
    # 看quant_ml有什么
    if os.path.exists(r'quant_ml'):
        print(f"  quant_ml contents: {os.listdir(r'quant_ml')}")