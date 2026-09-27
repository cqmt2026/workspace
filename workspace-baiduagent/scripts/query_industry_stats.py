#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询CRM数据库中行业分布和时间趋势
"""

import sqlite3
from datetime import datetime

DB_PATH = 'data/baidu_crm.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("=" * 60)
    print("重庆企业数据库行业分布分析")
    print("=" * 60)
    
    # 总客户数
    c.execute('SELECT COUNT(*) FROM customers')
    total = c.fetchone()[0]
    print(f"\n总客户数: {total}家")
    
    # 按年份统计新增
    print("\n【按年份新增统计】")
    c.execute('SELECT COUNT(*) FROM customers WHERE created_at >= "2024-01-01"')
    cnt_2024 = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM customers WHERE created_at >= "2025-01-01"')
    cnt_2025 = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM customers WHERE created_at >= "2026-01-01"')
    cnt_2026 = c.fetchone()[0]
    
    print(f"2024年以来新增: {cnt_2024}家")
    print(f"2025年以来新增: {cnt_2025}家")
    print(f"2026年以来新增: {cnt_2026}家")
    
    # 2025年以来行业TOP10
    print("\n【2025年以来新增行业TOP10】")
    c.execute('''
        SELECT industry, COUNT(*) as cnt 
        FROM customers 
        WHERE created_at >= "2025-01-01" 
        GROUP BY industry 
        ORDER BY cnt DESC 
        LIMIT 10
    ''')
    for i, r in enumerate(c.fetchall(), 1):
        print(f"  {i}. {r[0]}: {r[1]}家")
    
    # 全部数据中行业TOP15
    print("\n【全部行业TOP15】")
    c.execute('''
        SELECT industry, COUNT(*) as cnt 
        FROM customers 
        GROUP BY industry 
        ORDER BY cnt DESC 
        LIMIT 15
    ''')
    for i, r in enumerate(c.fetchall(), 1):
        pct = r[1] / total * 100
        print(f"  {i}. {r[0]}: {r[1]}家 ({pct:.1f}%)")
    
    # 按月份统计2025年新增
    print("\n【2025年月度新增趋势】")
    c.execute('''
        SELECT substr(created_at, 1, 7) as month, COUNT(*) as cnt
        FROM customers 
        WHERE created_at >= "2025-01-01" AND created_at < "2026-01-01"
        GROUP BY month
        ORDER BY month
    ''')
    for r in c.fetchall():
        print(f"  {r[0]}: {r[1]}家")
    
    # 按月份统计2026年新增
    print("\n【2026年月度新增趋势】")
    c.execute('''
        SELECT substr(created_at, 1, 7) as month, COUNT(*) as cnt
        FROM customers 
        WHERE created_at >= "2026-01-01"
        GROUP BY month
        ORDER BY month
    ''')
    for r in c.fetchall():
        print(f"  {r[0]}: {r[1]}家")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("分析完成")
    print("=" * 60)

if __name__ == '__main__':
    main()
