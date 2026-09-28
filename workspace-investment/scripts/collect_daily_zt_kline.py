#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collect_daily_zt_kline.py - 收集今日涨停K线数据，写入F:/market_data.db"""
import sys, os, io, sqlite3, time
from datetime import datetime, date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = r"F:\market_data.db"

def get_zt_stocks(trade_date):
    """获取涨停股列表"""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from scripts.data_api import DataAPI
    api = DataAPI()
    return api.get_zt_stocks(trade_date)

def get_stock_kline(code, trade_date):
    """获取某只股票的K线数据"""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from scripts.data_api import DataAPI
    api = DataAPI()
    klines = api.get_kline(code, days=10, end_date=trade_date)
    return [
        {
            'date': k['date'],
            'open': k['open'],
            'high': k['high'],
            'low': k['low'],
            'close': k['close'],
            'volume': k['volume'],
            'amount': k.get('amount', 0),
        }
        for k in klines
    ]

def save_kline(cursor, code, name, trade_date, klines):
    """将K线数据写入zt_kline表"""
    if not klines:
        return 0
    saved = 0
    for k in klines:
        try:
            cursor.execute(
                """INSERT OR REPLACE INTO zt_kline
                   (code, name, trade_date, k_date, open, high, low, close, volume, amount)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (code, name, trade_date, k["date"], k["open"], k["high"], k["low"], k["close"], k["volume"], k["amount"])
            )
            saved += 1
        except sqlite3.IntegrityError:
            pass
    return saved

def ensure_table(cursor):
    """确保zt_kline表存在"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zt_kline (
            code TEXT NOT NULL,
            name TEXT,
            trade_date TEXT NOT NULL,
            k_date TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume REAL, amount REAL,
            PRIMARY KEY (code, trade_date, k_date)
        )
    """)

def main():
    trade_date = date.today().strftime("%Y-%m-%d")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始收集涨停K线 | 交易日: {trade_date}")

    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ensure_table(cursor)
    conn.commit()

    # 获取今日涨停股
    zt_list = get_zt_stocks(trade_date)
    if not zt_list:
        print(f"今日({trade_date})无涨停股数据")
        conn.close()
        return

    print(f"今日涨停股数: {len(zt_list)}")
    total_saved = 0
    for stock in zt_list[:10]:  # 限制处理数量避免超时
        code = stock.get('code', '')
        name = stock.get('name', '')
        if not code:
            continue
        try:
            klines = get_stock_kline(code, trade_date)
            saved = save_kline(cursor, code, name or "", trade_date, klines)
            total_saved += saved
            if saved > 0:
                print(f"  {code} {name or ''}: 收集 {saved} 条K线")
        except Exception as e:
            print(f"  {code} 处理失败: {e}")
            time.sleep(1)  # 避免限流

    conn.commit()
    conn.close()
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 完成！共收集 {total_saved} 条涨停K线")

if __name__ == "__main__":
    main()
