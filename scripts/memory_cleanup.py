#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆库定期清理脚本
每周日22:00执行，清理过期临时文件
"""
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_DIR = Path(r"C:\Users\Administrator\.openclaw\workspace\memory")
TEMP_DIRS = ["temp", "__pycache__", ".dreams"]
MAX_AGE_DAYS = 30

def cleanup():
    """清理过期文件"""
    cleaned = 0
    cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)
    
    # 清理临时目录
    for temp_dir in TEMP_DIRS:
        path = MEMORY_DIR / temp_dir
        if path.exists():
            for f in path.glob("*"):
                if f.is_file() and f.stat().st_mtime < cutoff.timestamp():
                    f.unlink()
                    cleaned += 1
    
    # 清理过期日志
    log_dir = MEMORY_DIR / "日志"
    if log_dir.exists():
        for f in log_dir.rglob("*"):
            if f.is_file() and f.suffix in ['.txt', '.log']:
                if f.stat().st_mtime < cutoff.timestamp():
                    f.unlink()
                    cleaned += 1
    
    return cleaned

if __name__ == "__main__":
    count = cleanup()
    print(f"✅ 已清理 {count} 个过期文件")
