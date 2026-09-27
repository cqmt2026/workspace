#!/usr/bin/env python3
import re, os

html_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html"
root = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video"

with open(html_path, encoding="utf-8") as f:
    html = f.read()

imgs = re.findall(r'<img[^>]+>', html)
print(f"Total <img> tags: {len(imgs)}")
for img in imgs:
    src_match = re.search(r'src="([^"]+)"', img)
    if src_match:
        src = src_match.group(1)
        full = os.path.join(root, src)
        exists = os.path.exists(full)
        size = os.path.getsize(full) if exists else 0
        status = "OK" if exists and size > 1000 else "MISSING/TOO_SMALL"
        print(f"  [{status}] {src} ({size} bytes)")

# Check for invalid JS syntax
print("\n=== Checking inline script ===")
script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if script_match:
    script = script_match.group(1)
    print(f"Script length: {len(script)} chars")
    # Look for syntax errors
    lines = script.split('\n')
    for i, line in enumerate(lines[:50]):
        if 'invalid' in line.lower() or 'unexpected' in line.lower():
            print(f"  Line {i}: {line.strip()}")
    print(f"First 200 chars of script: {script[:200]}")
