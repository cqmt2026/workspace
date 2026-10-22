#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
benchmark_search.py - 检索性能基准测试
"""

import os
import sys
import time
import sqlite3

SM_DIR = r"C:\Users\Administrator\.openclaw\workspace\memory\supermemory_db"

def benchmark_like(query):
    """LIKE查询性能"""
    start = time.time()
    total = 0
    for db in os.listdir(SM_DIR):
        if not db.endswith('.db'):
            continue
        conn = sqlite3.connect(os.path.join(SM_DIR, db))
        c = conn.cursor()
        try:
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in c.fetchall()]
            for t in tables:
                if 'memory' in t.lower() and '_fts' not in t:
                    c.execute("SELECT COUNT(*) FROM [" + t + "] WHERE content LIKE '%" + query + "%'")
                    total += c.fetchone()[0]
        except:
            pass
        conn.close()
    elapsed = time.time() - start
    return total, elapsed

def benchmark_fts(query):
    """FTS查询性能"""
    start = time.time()
    total = 0
    for db in os.listdir(SM_DIR):
        if not db.endswith('.db'):
            continue
        conn = sqlite3.connect(os.path.join(SM_DIR, db))
        c = conn.cursor()
        try:
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'")
            fts_tables = [r[0] for r in c.fetchall()]
            for ft in fts_tables:
                c.execute("SELECT COUNT(*) FROM [" + ft + "] WHERE [" + ft + "] MATCH ?", (query,))
                total += c.fetchone()[0]
        except:
            pass
        conn.close()
    elapsed = time.time() - start
    return total, elapsed

def main():
    queries = ['RPS', '尾盘', 'Manim', '热点']
    
    print("="*60)
    print("检索性能基准测试")
    print("="*60)
    print()
    
    for q in queries:
        like_count, like_time = benchmark_like(q)
        fts_count, fts_time = benchmark_fts(q)
        
        speedup = like_time / fts_time if fts_time > 0 else 0
        
        print("查询: " + q)
        print("  LIKE: " + str(round(like_time*1000, 1)) + "ms, 结果: " + str(like_count))
        print("  FTS:  " + str(round(fts_time*1000, 1)) + "ms, 结果: " + str(fts_count))
        if speedup > 1:
            print("  加速: " + str(round(speedup, 1)) + "x")
        print()

if __name__ == "__main__":
    main()
