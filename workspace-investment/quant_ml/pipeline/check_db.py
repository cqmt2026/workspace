"""检查DB数据量"""
import sqlite3, time
conn = sqlite3.connect('F:/market_data.db')
t0 = time.time()
cur = conn.execute('SELECT COUNT(*) FROM daily_k WHERE date >= "2025-01-01"')
cnt = cur.fetchone()[0]
print(f'2025年后数据行数: {cnt}, 耗时: {time.time()-t0:.1f}s')

# 看volume有没有空值
cur2 = conn.execute('SELECT COUNT(*) FROM daily_k WHERE volume IS NULL OR volume = ""')
null_cnt = cur2.fetchone()[0]
print(f'volume空值: {null_cnt}')

# 看volume的dtype
cur3 = conn.execute('SELECT typeof(volume) FROM daily_k LIMIT 5')
for r in cur3:
    print(f'volume类型: {r[0]}')
conn.close()