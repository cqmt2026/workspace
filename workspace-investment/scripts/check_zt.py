import sqlite3
conn = sqlite3.connect('F:/market_data.db')
c = conn.cursor()
c.execute("SELECT date, COUNT(*) FROM zt_board WHERE date='2026-07-10'")
print('2026-07-10:', c.fetchall())
c.execute("SELECT MAX(date), COUNT(*) FROM zt_board")
print('max date:', c.fetchall())
# Also check what tables exist
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%zt%'")
print('zt tables:', c.fetchall())
conn.close()
