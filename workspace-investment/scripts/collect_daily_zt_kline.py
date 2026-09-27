#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collect_daily_zt_kline.py - 收集今日涨停K线数据（简化版）"""
import sys, os, io, sqlite3, time
from datetime import datetime, date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = r"F:\market_data.db"

def main():
    trade_date = date.today().strftime("%Y-%m-%d")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting collection for {trade_date}")
    
    if not os.path.exists(DB_PATH):
        print(f"DB not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zt_kline (
            code TEXT, name TEXT, trade_date TEXT, k_date TEXT,
            open REAL, high REAL, low REAL, close REAL, volume REAL, amount REAL,
            PRIMARY KEY (code, trade_date, k_date)
        )
    """)
    
    # TODO: 实际数据采集需接入数据源
    print("简化版：仅创建表结构，未接入数据源")
    print("需配置DataAPI后方可采集")
    
    conn.close()
    print("Done")

if __name__ == "__main__":
    main()
