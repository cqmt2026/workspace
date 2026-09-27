import json
from pathlib import Path
BASE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-pv\data\output\llm_generated")
with open(BASE / "llm_generated_20260820.json", "r", encoding="utf-8") as f:
    contents = json.load(f)
for i, c in enumerate(contents[:5]):
    body = c.get("body", "")
    hook = c.get("hook", "")
    cta = c.get("cta", "")
    chars = len(hook + body + cta)
    est_dur = chars / 5
    print(f"[{i+1}] {c['direction']:8s} | chars={chars:4d} | est_audio={est_dur:.0f}s")
    print(f"    hook: {hook[:40]}...")
    print(f"    body: {body[:80]}...")