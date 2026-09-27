# -*- coding: utf-8 -*-
"""
执行时间跟踪器
记录任务执行时间，支持规划能力评估
"""

import time
import json
import os
from datetime import datetime, timedelta
from functools import wraps

LOG_FILE = r"C:\Users\Administrator\.openclaw\workspace\memory\执行时间记录.json"

def timing_logger(func):
    """执行时间记录装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_ts = datetime.now().isoformat()
        
        print(f"[时间跟踪] 开始: {func.__name__} - {start_ts}")
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            status = "success"
            print(f"[时间跟踪] 完成: {func.__name__} - 耗时 {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            status = f"failed: {e}"
            print(f"[时间跟踪] 失败: {func.__name__} - 耗时 {elapsed:.2f}s - {e}")
            raise
        finally:
            # 记录时间
            record = {
                'function': func.__name__,
                'start': start_ts,
                'elapsed_seconds': round(elapsed, 2),
                'status': status
            }
            append_timing_record(record)
        
        return result
    
    return wrapper

def append_timing_record(record):
    """追加时间记录"""
    records = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except:
            records = []
    
    records.append(record)
    
    # 只保留最近100条
    records = records[-100:]
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def get_timing_stats(days=7):
    """获取统计信息"""
    if not os.path.exists(LOG_FILE):
        return {}
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    # 过滤最近N天的记录
    cutoff = datetime.now() - timedelta(days=days)
    recent = [r for r in records if datetime.fromisoformat(r['start']) > cutoff]
    
    # 按函数名分组统计
    stats = {}
    for r in recent:
        fname = r['function']
        if fname not in stats:
            stats[fname] = {'count': 0, 'total_time': 0, 'success': 0, 'failed': 0}
        stats[fname]['count'] += 1
        stats[fname]['total_time'] += r['elapsed_seconds']
        if 'success' in r['status']:
            stats[fname]['success'] += 1
        else:
            stats[fname]['failed'] += 1
    
    # 计算平均值
    for fname in stats:
        if stats[fname]['count'] > 0:
            stats[fname]['avg_time'] = round(stats[fname]['total_time'] / stats[fname]['count'], 2)
            stats[fname]['success_rate'] = round(stats[fname]['success'] / stats[fname]['count'] * 100, 1)
    
    return stats

# 使用示例
if __name__ == "__main__":
    @timing_logger
    def slow_function():
        time.sleep(1)
        return "done"
    
    @timing_logger
    def fast_function():
        return "quick"
    
    slow_function()
    fast_function()
    
    stats = get_timing_stats()
    print("\n=== 执行时间统计 ===")
    for func, stat in stats.items():
        print(f"{func}: {stat['count']}次, 平均{stat['avg_time']}s, 成功率{stat['success_rate']}%")
