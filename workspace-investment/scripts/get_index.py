# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import sqlite3

conn = sqlite3.connect(r'F:\market_data.db')
c = conn.cursor()

# 查看表结构
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Tables:", tables)

# 查看daily_index结构
if 'daily_index' in tables:
    c.execute("PRAGMA table_info(daily_index)")
    cols = [r[1] for r in c.fetchall()]
    print("daily_index columns:", cols)
    c.execute("SELECT * FROM daily_index ORDER BY date DESC LIMIT 5")
    rows = c.fetchall()
    for r in rows:
        print(r)

# 查看daily_zt表
if 'daily_zt' in tables:
    c.execute("SELECT * FROM daily_zt ORDER BY date DESC LIMIT 3")
    rows = c.fetchall()
    print("\ndaily_zt latest:")
    for r in rows:
        print(r)

conn.close()
