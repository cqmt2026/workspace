# -*- coding: utf-8 -*-
import os, json
from datetime import datetime

# Check task logs for today
log_dir = r'C:\Users\Administrator\.openclaw\workspace\memory\日志\task'
today = '2026-08-13'
print(f"=== Task logs for {today} ===")
found = False
for root, dirs, files in os.walk(log_dir):
    for fn in files:
        if fn.endswith('.jsonl'):
            try:
                with open(os.path.join(root, fn), encoding='utf-8', errors='ignore') as fh:
                    for line in fh:
                        try:
                            e = json.loads(line.strip())
                            if today in e.get('timestamp', ''):
                                print(f"{e.get('timestamp')} | {e.get('status')} | {e.get('task','')}")
                                found = True
                        except:
                            pass
            except:
                pass
if not found:
    print("No task logs found for today")

# Check recent log files
print(f"\n=== Recent log files ===")
all_logs = []
for root, dirs, files in os.walk(log_dir):
    for fn in files:
        if fn.endswith('.jsonl'):
            fp = os.path.join(root, fn)
            mt = datetime.fromtimestamp(os.path.getmtime(fp))
            all_logs.append((mt, fp, fn))
all_logs.sort(reverse=True)
for mt, fp, fn in all_logs[:15]:
    print(f"{mt.strftime('%m-%d %H:%M')} {fn}")
