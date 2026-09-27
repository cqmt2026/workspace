import json, os

cb_path = r"C:\Users\Administrator\.openclaw\workspace\logs\cron_failure_state.json"
with open(cb_path, "r", encoding="utf-8", errors="replace") as f:
    data = json.load(f)
print(f"Circuit breaker entries: {len(data)}")
print("Self-Learning state:", data.get("Self-Learning-统一学习", "not found"))

# Check recent failures
log_dir = r"C:\Users\Administrator\.openclaw\workspace\memory\日志\task\2026\08\all"
for fn in sorted(os.listdir(log_dir)):
    fp = os.path.join(log_dir, fn)
    with open(fp, "r", encoding="utf-8") as f:
        for line in f:
            if "Self-Learning" in line:
                r = json.loads(line)
                ts = r.get("timestamp", "")[:19]
                st = r.get("status", "")
                err = r.get("error", "")[:100]
                det = r.get("detail", "")[:100]
                print(f"{ts} | {st} | err={err} | detail={det}")
