# -*- coding: utf-8 -*-
import sqlite3, sys
from pathlib import Path
BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))

db_path = BASE / "data" / "pv.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("=== Duplicate titles ===")
cur.execute("""
    SELECT title, source, collected_at FROM hot_topics
    WHERE title IN (
        SELECT title FROM hot_topics GROUP BY title HAVING COUNT(*) > 1
    ) ORDER BY title
""")
dupes = cur.fetchall()
print(f"Found {len(dupes)} duplicate entries")
for d in dupes:
    print(f"  [{d[1]}] {d[0][:55]} at {d[2]}")

print("\n=== Latest 10 entries ===")
cur.execute("""
    SELECT title, source, collected_at FROM hot_topics
    ORDER BY collected_at DESC LIMIT 10
""")
for r in cur.fetchall():
    print(f"  [{r[1]}] {r[0][:55]} at {r[2]}")

# Check if solarbe and bjx share same titles
print("\n=== Cross-source duplicates (solarbe vs bjx) ===")
cur.execute("""
    SELECT a.title, a.source as src1, b.source as src2, a.collected_at
    FROM hot_topics a JOIN hot_topics b
    ON a.title = b.title AND a.source != b.source
    WHERE a.source IN ('solarbe', 'bjx') AND b.source IN ('solarbe', 'bjx')
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"  '{r[0][:50]}' -> {r[1]} + {r[2]}")

conn.close()
