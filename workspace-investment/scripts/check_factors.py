import sqlite3
conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\factors.db')
# Check latest dates
rows = conn.execute("SELECT date, COUNT(*) FROM factors GROUP BY date ORDER BY date DESC LIMIT 10").fetchall()
print("Factors DB latest dates:")
for r in rows:
    print(f"  {r[0]}: {r[1]} factors")
conn.close()
