#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collect_daily_zt_kline.py - 收集今日涨停K线数据"""
import sys, os, io, sqlite3, time
from datetime import datetime, date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = r"F:\market_data.db"

def retry(max_attempts=3, delay=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_attempts - 1:
                        raise
                    print(f"Retry {i+1}/{max_attempts}: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry
def get_zt_stocks(trade_date):
    from scripts.data_api import DataAPI
    return DataAPI.get_zt_stocks(trade_date)

def main():
    trade_date = date.today().strftime("%Y-%m-%d")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting collection for {trade_date}")
    
    if not os.path.exists(DB_PATH):
        print(f"DB not found: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zt_kline (
            code TEXT, name TEXT, trade_date TEXT, k_date TEXT,
            open REAL, high REAL, low REAL, close REAL, volume REAL, amount REAL,
            PRIMARY KEY (code, trade_date, k_date)
        )
    """)
    
    try:
        zt_list = get_zt_stocks(trade_date)
        print(f"ZT stocks: {len(zt_list)}")
        
        for code, name in zt_list[:5]:  # Limit for test
            print(f"Processing {code} {name}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
