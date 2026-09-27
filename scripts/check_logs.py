import os, json

log_base = r"C:\Users\Administrator\.openclaw\workspace\memory\日志\task"
dirs = sorted([d for d in os.listdir(log_base) if os.path.isdir(os.path.join(log_base, d))], reverse=True)[:3]
print("Recent date dirs:", dirs)
for d in dirs:
    mm_dirs = sorted(os.listdir(os.path.join(log_base, d)), reverse=True)[:3]
    for m in mm_dirs:
        all_dir = os.path.join(log_base, d, m, "all")
        if os.path.isdir(all_dir):
            files = sorted(os.listdir(all_dir), reverse=True)[:3]
            for f in files:
                fpath = os.path.join(all_dir, f)
                print(f"\n--- {f} ---")
                with open(fpath, "r", encoding="utf-8") as fh:
                    lines = fh.readlines()[-10:]
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            r = json.loads(line)
                            ts = r.get("timestamp", "")[:19]
                            task = r.get("task", "")[:40]
                            status = r.get("status", "")
                            error = r.get("error", "")[:60]
                            print(f"  {ts} | {task:40s} | {status:8s} | {error}")
                        except:
                            print(f"  {line[:120]}")

# check circuit breaker
cb_path = os.path.join(os.path.dirname(log_base), "circuit_breaker.json")
if os.path.exists(cb_path):
    with open(cb_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("\nCircuit breaker state:")
    for k, v in data.items():
        if "self" in k.lower() or "learn" in k.lower():
            print(f"  {k}: {v}")
else:
    print("\nNo circuit breaker file found")
