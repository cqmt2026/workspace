#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百都搭档使用记录脚本
每次使用后调用，自动追加今日记录
"""
import os
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(r"C:\Users\Administrator\.openclaw\workspace\memory\baidu")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
log_file = MEMORY_DIR / f"usage_{today}.md"

def append_record(section, content):
    """追加记录到今日文件"""
    if not log_file.exists():
        # 创建新文件
        content = f"# 百都搭档使用记录 - {today}\n\n## {section}\n{content}\n"
    else:
        # 追加到对应section
        content = f"\n## {section}\n{content}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        section = sys.argv[1]
        data = sys.stdin.read()
        append_record(section, data)
        print(f"✅ 已记录到 {log_file}")
