# -*- coding: utf-8 -*-
import sqlite3, sys
from pathlib import Path
BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))

db_path = BASE / "data" / "pv.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("=== All PV-related topics ===")
cur.execute("""
    SELECT title, source, pv_score, collected_at FROM hot_topics
    WHERE pv_related = 1 ORDER BY collected_at DESC
""")
rows = cur.fetchall()
print(f"Total PV topics: {len(rows)}")
for r in rows:
    print(f"  [{r[1]}] pv={r[2]:.2f} {r[0][:55]} at {r[3]}")

print("\n=== Policies ===")
cur.execute("""
    SELECT title, level, policy_type, province, collected_at FROM policies
    ORDER BY collected_at DESC
""")
rows2 = cur.fetchall()
print(f"Total policies: {len(rows2)}")
for r in rows2:
    print(f"  [{r[1]}/{r[2]}] {r[0][:55]} at {r[4]}")

# Check for cross-source duplicates (same title, different source)
print("\n=== Cross-source same titles ===")
cur.execute("""
    SELECT title, GROUP_CONCAT(source) as sources
    FROM hot_topics GROUP BY title HAVING sources LIKE '%,%'
""")
dupes = cur.fetchall()
print(f"Cross-source duplicates: {len(dupes)}")
for d in dupes:
    print(f"  '{d[0][:50]}' -> {d[1]}")

conn.close()
