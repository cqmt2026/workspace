#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gateway_monitor.py - Gateway监控脚本

功能：
1. 监控Gateway响应时间
2. 记录性能指标
3. 生成性能报告

用法：
    python gateway_monitor.py --measure
    python gateway_monitor.py --report
"""

import os
import sys
import json
import time
import urllib.request
import statistics
from datetime import datetime, timedelta

BASE = r"C:\Users\Administrator\.openclaw"
LOG_DIR = os.path.join(BASE, "workspace", "logs")
REPORT_DIR = os.path.join(BASE, "workspace", "memory", "性能监控")

def measure_latency(port=18789, iterations=10):
    """测量Gateway响应时间"""
    url = f"http://127.0.0.1:{port}/health"
    latencies = []
    
    print(f"测量Gateway响应时间 ({iterations}次)...")
    
    for i in range(iterations):
        start = time.time()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'GatewayMonitor/1.0'})
            resp = urllib.request.urlopen(req, timeout=5)
            elapsed = (time.time() - start) * 1000  # 转换为毫秒
            latencies.append(elapsed)
            print(f"  [{i+1}/{iterations}] {elapsed:.1f}ms")
        except Exception as e:
            print(f"  [{i+1}/{iterations}] ERROR: {e}")
    
    if latencies:
        result = {
            'timestamp': datetime.now().isoformat(),
            'port': port,
            'iterations': len(latencies),
            'min_ms': min(latencies),
            'max_ms': max(latencies),
            'avg_ms': statistics.mean(latencies),
            'median_ms': statistics.median(latencies),
            'stdev_ms': statistics.stdev(latencies) if len(latencies) > 1 else 0
        }
        
        # 保存结果
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file = os.path.join(LOG_DIR, f"gateway_latency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        print()
        print(f"结果已保存: {log_file}")
        print(f"平均响应时间: {result['avg_ms']:.1f}ms")
        return result
    else:
        print("测量失败")
        return None

def generate_report(days=7):
    """生成性能报告"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    # 查找最近的日志文件
    log_files = []
    for f in os.listdir(LOG_DIR):
        if f.startswith('gateway_latency_') and f.endswith('.json'):
            log_files.append(os.path.join(LOG_DIR, f))
    
    if not log_files:
        print("没有找到历史数据")
        return
    
    # 按时间排序
    log_files.sort()
    
    # 读取最近的数据
    reports = []
    cutoff = datetime.now() - timedelta(days=days)
    
    for f in log_files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                ts = datetime.fromisoformat(data['timestamp'])
                if ts >= cutoff:
                    reports.append(data)
        except:
            pass
    
    if not reports:
        print("最近" + str(days) + "天没有数据")
        return
    
    # 生成统计
    avg_times = [r['avg_ms'] for r in reports]
    
    report = {
        'period': f'最近{days}天',
        'sample_count': len(reports),
        'avg_latency_ms': statistics.mean(avg_times),
        'min_latency_ms': min(avg_times),
        'max_latency_ms': max(avg_times),
        'trend': 'stable' if statistics.stdev(avg_times) < 10 else 'varying'
    }
    
    # 保存报告
    report_file = os.path.join(REPORT_DIR, f"gateway_report_{datetime.now().strftime('%Y%m%d')}.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print("=== Gateway性能报告 ===")
    print(f"周期: {report['period']}")
    print(f"样本数: {report['sample_count']}")
    print(f"平均响应: {report['avg_latency_ms']:.1f}ms")
    print(f"最快: {report['min_latency_ms']:.1f}ms")
    print(f"最慢: {report['max_latency_ms']:.1f}ms")
    print(f"趋势: {report['trend']}")
    print()
    print(f"报告已保存: {report_file}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Gateway监控工具')
    parser.add_argument('--measure', action='store_true', help='测量响应时间')
    parser.add_argument('--report', action='store_true', help='生成性能报告')
    parser.add_argument('--days', type=int, default=7, help='报告天数')
    args = parser.parse_args()
    
    if args.measure:
        measure_latency()
    elif args.report:
        generate_report(args.days)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
