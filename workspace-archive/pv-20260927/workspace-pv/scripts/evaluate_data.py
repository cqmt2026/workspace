# -*- coding: utf-8 -*-
"""评估现有数据库数据价值"""
import os, sys, sqlite3
from pathlib import Path
BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

conn = sqlite3.connect(str(BASE / "data" / "pv.db"))
cur = conn.cursor()

print("=== Table counts ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
for t in [r[0] for r in cur.fetchall()]:
    cnt = cur.execute(f'SELECT COUNT(*) FROM [{t}]').fetchone()[0]
    print(f"  {t}: {cnt}")

print("\n=== PV topics (latest 10) ===")
cur.execute("""SELECT title, source, pv_score, collected_at FROM hot_topics
               WHERE pv_related=1 ORDER BY collected_at DESC LIMIT 10""")
for r in cur.fetchall():
    print(f"  [{r[1]}] pv={r[2]:.2f} {r[0][:50]} at {r[3]}")

print("\n=== Policies (latest 10) ===")
cur.execute("""SELECT title, level, policy_type, province, collected_at FROM policies
               ORDER BY collected_at DESC LIMIT 10""")
for r in cur.fetchall():
    print(f"  [{r[1]}/{r[2]}] {r[0][:50]} at {r[4]}")

# Cross-source duplicates
print("\n=== Cross-source duplicates ===")
cur.execute("""SELECT title, GROUP_CONCAT(source) as sources
               FROM hot_topics GROUP BY title HAVING sources LIKE '%,%'""")
for r in cur.fetchall():
    print(f"  '{r[0][:50]}' -> {r[1]}")

conn.close()
