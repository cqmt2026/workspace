#!/usr/bin/env python3
# 自动git提交脚本
import subprocess
import sys
from datetime import datetime

def auto_commit(message):
    try:
        subprocess.run(["git", "add", "-A"], check=True, cwd=r"C:\Users\Administrator\.openclaw\workspace")
        subprocess.run(["git", "commit", "-m", message], check=True, cwd=r"C:\Users\Administrator\.openclaw\workspace")
        print(f"✅ 已提交: {message}")
        return True
    except Exception as e:
        print(f"⚠️ 提交失败: {e}")
        return False

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else f"auto: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    sys.exit(0 if auto_commit(msg) else 1)
