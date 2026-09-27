# -*- coding: utf-8 -*-
import sqlite3
db=sqlite3.connect('F:/market_data.db')
cur=db.cursor()
# 查上证指数K线
rows=cur.execute("SELECT date, close FROM daily_k WHERE code='sh000001' ORDER BY date DESC LIMIT 10").fetchall()
print('上证指数K线:')
for r in rows:
    print(f'  {r[0]}: {r[1]}')
print()
# 看看有哪些指数代码
codes=cur.execute("SELECT DISTINCT code FROM daily_k WHERE code LIKE 'sh%' LIMIT 20").fetchall()
print('sh开头代码:', [c[0] for c in codes])
db.close()