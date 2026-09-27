# -*- coding: utf-8 -*-
"""修复素材文件名（去空格）+ 重新生成V5"""
import os, shutil, subprocess
from pathlib import Path

BASE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-pv\data\materials")

# 重命名所有带空格的素材
renamed = []
for f in BASE.glob("*.mp4"):
    name = f.name
    new_name = name.replace(" ", "_")
    if name != new_name:
        new_path = BASE / new_name
        shutil.copy2(str(f), str(new_path))
        renamed.append((name, new_name))
        print(f"Copy: {name} -> {new_name}")

print(f"\nRenamed/Copied {len(renamed)} files")
print("Now re-running batch generation with fixed names...")
