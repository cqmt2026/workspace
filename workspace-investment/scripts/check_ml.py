import sqlite3
conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\factors.db')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM factors WHERE factor_name='ml_prob_lgb'")
print('ml_prob_lgb total:', c.fetchone()[0])
c.execute("SELECT DISTINCT date FROM factors WHERE factor_name='ml_prob_lgb' ORDER BY date DESC LIMIT 3")
print('Latest dates:', [r[0] for r in c.fetchall()])
c.execute("SELECT COUNT(*) FROM factors WHERE factor_name='ml_prob_lgb' AND date='2026-08-27'")
print('2026-08-27 count:', c.fetchone()[0])
c.execute("SELECT code, value FROM factors WHERE factor_name='ml_prob_lgb' AND date='2026-08-27' ORDER BY value DESC LIMIT 5")
print('Top5:')
for row in c.fetchall():
    print(f'  {row[0]}: {row[1]:.4f}')
conn.close()
