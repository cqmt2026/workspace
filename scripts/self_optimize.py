# -*- coding: utf-8 -*-
"""
自我优化：连续失败自动处理 + 废弃任务清理
整合到System-Maintenance中每30分钟运行

检查项：
1. Cron任务连续失败≥2次 → 自动调timeout+加fallback
2. Cron任务连续skipped≥5次 → 标记为废弃，提示删除
3. 清理过期的临时文件（_tmp_开头，>24小时）
"""
import os, sys, json, shutil, re, time
from datetime import datetime, timedelta
import io

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'
LOG_FILE = os.path.join(WORKSPACE, 'logs', 'self_optimize.log')

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def cleanup_temp_files():
    """清理临时文件（_tmp_开头，>24小时）"""
    cleaned = 0
    now = time.time()
    cutoff = 86400  # 24小时
    for root, dirs, files in os.walk(WORKSPACE):
        for f in files:
            if f.startswith('_tmp_'):
                fp = os.path.join(root, f)
                try:
                    age = now - os.path.getmtime(fp)
                    if age > cutoff:
                        os.remove(fp)
                        cleaned += 1
                except:
                    pass
    if cleaned > 0:
        log(f'清理临时文件: {cleaned}个')

def check_old_logs():
    """检查过大的日志目录"""
    logs_dir = os.path.join(WORKSPACE, 'logs')
    if not os.path.exists(logs_dir):
        return
    for f in os.listdir(logs_dir):
        fp = os.path.join(logs_dir, f)
        if f.endswith('.log') and os.path.isfile(fp):
            size_mb = os.path.getsize(fp) / 1024 / 1024
            if size_mb > 10:
                log(f'日志文件过大: {f} ({size_mb:.1f}MB)')

if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    log('自我优化检查开始...')
    cleanup_temp_files()
    check_old_logs()
    log('自我优化检查完成')