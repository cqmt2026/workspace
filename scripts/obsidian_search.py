#!/usr/bin/env python3
import io
import sys, os, re

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.stdout.reconfigure(encoding="utf-8")
BASE = r"F:\.Obsidian\Jarvis"
q = " ".join(sys.argv[1:]) if len(sys.argv)>1 else input("搜索: ")
res = []
for root,_,files in os.walk(BASE):
    if ".obsidian" in root or ".git" in root: continue
    for fn in files:
        if not fn.endswith(".md"): continue
        fp = os.path.join(root, fn)
        try:
            c = open(fp, "r", encoding="utf-8").read()
        except: continue
        if q.lower() in c.lower():
            rel = os.path.relpath(fp, BASE)
            res.append(rel)
print("\n".join(res[:20]))
