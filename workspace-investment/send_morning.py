#!/usr/bin/env python3
import subprocess
import os
import sys

TARGET = "o9cq8092w_2W-BHmLsGGbleQEHKg@im.wechat"
OPENCLAW_PATH = r"C:\Users\Administrator\AppData\Roaming\npm\openclaw.cmd"

# Read the summary file
summary_file = "morning_summary.txt"
with open(summary_file, "r", encoding="utf-8") as f:
    text = f.read()

print(f"Sending message with {len(text)} characters...")

# Try to run via cmd/c to handle the .cmd file properly
cmd_str = f'"{OPENCLAW_PATH}" message send --target "{TARGET}" --message "{text}"'
result = subprocess.run(
    cmd_str,
    shell=True,
    capture_output=True,
    text=True,
    timeout=60
)

print("Return code:", result.returncode)
if result.stdout:
    print("Stdout:", result.stdout[:500])
if result.stderr:
    print("Stderr:", result.stderr[:500])

sys.exit(result.returncode)