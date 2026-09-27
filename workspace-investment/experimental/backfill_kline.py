# -*- coding: utf-8 -*-
"""
DB数据补充 — 腾讯API批量回补K线
=================================
目标：补充K线<65条的股票到至少65条
方法：腾讯API ff_dayk 接口获取历史K线

补充策略：
  1. 按数据量从少到多补充（最缺的优先）
  2. 每次补充到65条（或所有可用数据）
  3. 批量写入DB
"""
import sqlite3, sys, time, json, requests
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

DB = r'F:\market_data.db'
TARGET = 65  # 目标K线数

t0 = time.time()

print("=" * 60)
print("DB数据补充 — 腾讯API批量回补")
print("=" * 60)

conn = sqlite3.connect(DB)

# 1. 找出数据不足的股票
print("\n[1] 分析数据缺口")
print("-" * 60)

# 排除指数和bj
short_codes = conn.execute("""
    SELECT code, COUNT(*) as cnt FROM daily_k 
    WHERE code NOT LIKE 'bj.%' 
    AND code NOT LIKE 'sh.000%' 
    AND code NOT LIKE 'sh.300%' 
    AND code NOT LIKE 'sh.88%'
    AND code NOT LIKE 'sz.399%'
    AND code NOT LIKE 'sh.8%'
    GROUP BY code HAVING cnt < ?
    ORDER BY cnt ASC
""", (TARGET,)).fetchall()

print(f"K线<{TARGET}条的股票: {len(short_codes)}只", flush=True)

# 按缺口分组
gaps = {}
for code, cnt in short_codes:
    gap = TARGET - cnt
    if gap not in gaps:
        gaps[gap] = 0
    gaps[gap] += 1

for gap in sorted(gaps.keys()):
    print(f"  缺口{gap}条: {gaps[gap]}只")

# 只补充有>=5条数据的（太少的补了也没意义）
fillable = [(code, cnt) for code, cnt in short_codes if cnt >= 5]
print(f"\n可补充(>=5条): {len(fillable)}只")
print(f"跳过(<5条): {len(short_codes) - len(fillable)}只")

# 获取每只股票的最新日期
print("\n[2] 检查各股票最新日期")
print("-" * 60)

code_info = []
for code, cnt in fillable:
    last_date = conn.execute(
        "SELECT MAX(date) FROM daily_k WHERE code=?", (code,)
    ).fetchone()[0]
    code_info.append((code, cnt, last_date))

# 按缺口从大到小排序（最缺的优先补）
code_info.sort(key=lambda x: x[1])

print(f"前10只（最缺数据）:")
for code, cnt, last_date in code_info[:10]:
    print(f"  {code}: {cnt}条, 最新: {last_date}")

# 2. 批量补充
print(f"\n[3] 腾讯API批量回补")
print("-" * 60)

def fetch_kline_from_tencent(code):
    """
    腾讯API获取日K线（ifzq.gtimg.cn）
    格式: sh600376 → {"data": {"sh600376": {"qfqday": [[date, open, close, high, low, volume], ...]}}}
    返回: [(date, open, close, high, low, volume), ...]
    """
    clean = code.split('.')[-1]
    prefix = 'sh' if code.startswith('sh.') else 'sz'
    symbol = f'{prefix}{clean}'
    url = f'http://ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,65,qfq'
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code != 200:
            return None
        
        data = r.json()
        if data.get('code') != 0:
            return None
        
        # 腾讯返回格式：day（前复权）或 qfqday（全复权）
        stock_data = data.get('data', {}).get(symbol, {})
        day_data = stock_data.get('qfqday') or stock_data.get('day') or []
        if not day_data:
            return None
        
        records = []
        for item in day_data:
            if len(item) >= 6:
                try:
                    records.append((
                        item[0],  # date: '2026-03-30'
                        float(item[2]),  # close (腾讯顺序: date, open, close, high, low, volume)
                        float(item[1]),  # open
                        float(item[3]),  # high
                        float(item[4]),  # low
                        float(item[5]),  # volume
                    ))
                except (ValueError, IndexError):
                    continue
        
        if records:
            records.sort(key=lambda x: x[0])
            return records
    except Exception as e:
        pass
    return None

def insert_kline(code, records):
    """批量插入K线数据"""
    if not records:
        return 0
    
    cursor = conn.cursor()
    inserted = 0
    for rec in records:
        date_str, close_p, open_p, high_p, low_p, volume = rec
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO daily_k 
                (code, date, open, close, high, low, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (code, date_str, open_p, close_p, high_p, low_p, volume))
            if cursor.rowcount > 0:
                inserted += 1
        except:
            pass
    
    conn.commit()
    return inserted

# 分批补充
total_filled = 0
total_attempted = 0
total_errors = 0
BATCH_SIZE = 50

print(f"开始补充 {len(code_info)} 只股票...")
print(f"每批{BATCH_SIZE}只，分批提交...")

for batch_start in range(0, len(code_info), BATCH_SIZE):
    batch = code_info[batch_start:batch_start + BATCH_SIZE]
    batch_filled = 0
    
    for code, cnt, last_date in batch:
        total_attempted += 1
        
        records = fetch_kline_from_tencent(code)
        if not records:
            total_errors += 1
            if total_errors <= 5:
                print(f"  ❌ {code}: 获取失败")
            continue
        
        # 只补充DB中不存在的日期
        existing_dates = set(r[0] for r in conn.execute(
            "SELECT date FROM daily_k WHERE code=?", (code,)
        ).fetchall())
        
        new_records = [r for r in records if r[0] not in existing_dates]
        if not new_records:
            continue
        
        filled = insert_kline(code, new_records)
        if filled > 0:
            batch_filled += filled
            total_filled += filled
        
        time.sleep(0.1)  # 防封
    
    elapsed = time.time() - t0
    print(f"  批次{batch_start//BATCH_SIZE + 1}: +{batch_filled}条 (累计{total_filled}条, {total_attempted}/{len(code_info)}只, {elapsed:.0f}s)")

# 3. 验证
print(f"\n{'='*60}")
print(f"[4] 验证结果")
print('='*60)

remaining = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT code, COUNT(*) as cnt FROM daily_k 
        WHERE code NOT LIKE 'bj.%' 
        AND code NOT LIKE 'sh.000%' 
        AND code NOT LIKE 'sh.300%' 
        AND code NOT LIKE 'sh.88%'
        AND code NOT LIKE 'sz.399%'
        AND code NOT LIKE 'sh.8%'
        GROUP BY code HAVING cnt < ?
    )
""", (TARGET,)).fetchone()[0]

print(f"补充前: {len(short_codes)}只不足")
print(f"尝试补充: {total_attempted}只")
print(f"成功补充: {total_filled}条K线")
print(f"补充后仍不足: {remaining}只")
print(f"总耗时: {time.time()-t0:.0f}s")

# 检查ML可用股票数
ml_ready = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT code, COUNT(*) as cnt FROM daily_k 
        WHERE code NOT LIKE 'bj.%' 
        AND code NOT LIKE 'sh.000%' 
        AND code NOT LIKE 'sh.300%' 
        AND code NOT LIKE 'sh.88%'
        AND code NOT LIKE 'sz.399%'
        AND code NOT LIKE 'sh.8%'
        GROUP BY code HAVING cnt >= ?
    )
""", (TARGET,)).fetchone()[0]

print(f"ML可用股票(K线>={TARGET}): {ml_ready}只")

conn.close()
print(f"\n完成!")