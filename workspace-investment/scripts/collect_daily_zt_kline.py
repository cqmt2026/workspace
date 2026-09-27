#!/usr/bin/env python3
"""
collect_daily_zt_kline.py
收集今日涨停股K线数据，写入数据库 F:/market_data.db
"""

import io
import sys
import os
import sqlite3
from datetime import datetime, date

# 确保能找到项目模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# 数据库路径
DB_PATH = r"F:\market_data.db"


def get_today_str():
    """返回今日日期字符串 YYYY-MM-DD（与DB格式一致）"""
    return date.today().strftime("%Y-%m-%d")


def get_zt_stocks(cursor, trade_date):
    """从涨停表获取今日涨停股票列表"""
    from scripts.data_api import DataAPI
    stocks = DataAPI.get_zt_stocks(trade_date)
    return [(s['code'], s['name']) for s in stocks]


def get_stock_kline(cursor, code, trade_date):
    """获取某只股票的历史K线（用于涨停分析）"""
    from scripts.data_api import DataAPI
    klines = DataAPI.get_kline(code, days=10, end_date=trade_date)
    return [
        {
            'date': k['date'],
            'open': k['open'],
            'high': k['high'],
            'low': k['low'],
            'close': k['close'],
            'volume': k['volume'],
            'amount': 0,
        }
        for k in klines
    ]



def save_kline(cursor, code, name, trade_date, klines):
    """将K线数据写入 zt_kline 表"""
    if not klines:
        return 0

    saved = 0
    for k in klines:
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO zt_kline
                    (code, name, trade_date, k_date, open, high, low, close, volume, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    code,
                    name,
                    trade_date,
                    k["date"],
                    k["open"],
                    k["high"],
                    k["low"],
                    k["close"],
                    k["volume"],
                    k["amount"],
                ),
            )
            saved += 1
        except sqlite3.IntegrityError:
            pass
    return saved


def ensure_table(cursor):
    """确保 zt_kline 表存在"""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS zt_kline (
            code        TEXT NOT NULL,
            name        TEXT,
            trade_date  TEXT NOT NULL,
            k_date      TEXT NOT NULL,
            open        REAL,
            high        REAL,
            low         REAL,
            close       REAL,
            volume      REAL,
            amount      REAL,
            PRIMARY KEY (code, trade_date, k_date)
        )
        """
    )


def main():
    trade_date = get_today_str()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始收集涨停K线 | 交易日: {trade_date}")

    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 确保表存在
    ensure_table(cursor)
    conn.commit()

    # 获取今日涨停股
    zt_list = get_zt_stocks(cursor, trade_date)
    if not zt_list:
        print(f"今日({trade_date})无涨停记录")
        conn.close()
        return

    print(f"今日涨停股票数: {len(zt_list)}")

    total_saved = 0
    for code, name in zt_list:
        klines = get_stock_kline(cursor, code, trade_date)
        saved = save_kline(cursor, code, name or "", trade_date, klines)
        total_saved += saved
        if saved > 0:
            print(f"  {code} {name or ''}: 收集 {saved} 条K线")

    conn.commit()
    conn.close()

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 完成！共收集 {total_saved} 条涨停K线")


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    main()