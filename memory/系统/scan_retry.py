import json, os

workspace = r"C:\Users\Administrator\.openclaw\workspace"
patterns = ["retry", "错题", "error", "fail"]

for root, dirs, files in os.walk(workspace):
    dirs[:] = [d for d in dirs if d not in ["node_modules", ".git", "__pycache__"]]
    for f in files:
        lower = f.lower()
        if any(p in lower for p in patterns):
            full = os.path.join(root, f)
            print(full)