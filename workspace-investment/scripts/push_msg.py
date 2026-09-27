#!/usr/bin/env python3
import subprocess, os, sys

TARGET = "o9cq8092w_2W-BHmLsGGbleQEHKg@im.wechat"

msg = """📰 晚间资讯分类 · 2026-08-30 22:01

共抓取20条（东财快讯20 + 东财A股0 + 新华0）

🚨 P0 紧急 (0条) ✅ 无紧急事项

📋 P1 重要 (0条)

📝 P3 观察 (5条精选)
• 美联储主席沃什：2%通胀目标坚定且固定
• 美国8月非农就业人数修订下调7.9万人
• 美国8月密歇根大学消费者信心指数终值51.7
• 美国8月芝加哥PMI 47.1，远低于预期57.9
• 美国8月一年期通胀率预期4%，预期4.40%

_P0=5分钟内响应 / P1=当日处理 / P2=次日参考 / P3=长期观察_"""

openclaw = os.path.join(os.environ.get('APPDATA', ''), 'npm', 'openclaw.cmd')
args = [openclaw, 'message', 'send', '--channel', 'wechat', '--target', TARGET, '--message', msg]
for i in range(3):
    try:
        r = subprocess.run(args, capture_output=True, timeout=30, encoding='utf-8', errors='replace')
        print(f"Return: {r.returncode}")
        print(f"Stdout: {r.stdout[:200]}")
        print(f"Stderr: {r.stderr[:200]}")
        if r.returncode == 0:
            print("[OK] Sent")
            sys.exit(0)
        print(f"[WARN] Attempt {i+1} failed, retrying...")
        import time; time.sleep(2)
    except subprocess.TimeoutExpired:
        print(f"[WARN] Attempt {i+1} timeout, retrying...")
        import time; time.sleep(2)
    except Exception as e:
        print(f"[WARN] Attempt {i+1} error: {e}")
        import time; time.sleep(2)
print("[FAIL] All attempts exhausted")