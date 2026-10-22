#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
search_performance.py - 知识检索性能监控

功能：
1. 测试Supermemory搜索速度
2. 测试Obsidian搜索速度  
3. 对比两种方式的命中率
4. 生成性能报告

用法：
    python search_performance.py
"""

import os
import sys
import time
import sqlite3
from datetime import datetime
from typing import List, Tuple

# 路径配置
SM_DIR = r"C:\Users\Administrator\.openclaw\workspace\memory\supermemory_db"
OBSIDIAN_DIR = r"F:\Obsidian\Jarvis"
LOG_DIR = r"C:\Users\Administrator\.openclaw\workspace\memory\日志\performance"

def test_supermemory_search(query: str, top_k: int = 5) -> Tuple[List[str], float]:
    """测试Supermemory搜索性能"""
    start = time.time()
    results = []
    
    # 遍历所有数据库
    for db_file in os.listdir(SM_DIR):
        if not db_file.endswith('.db'):
            continue
        db_path = os.path.join(SM_DIR, db_file)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # LIKE查询（当前实现）
            cursor.execute(
                f"SELECT content FROM memory WHERE content LIKE '%{query}%' LIMIT {top_k}",
            )
            rows = cursor.fetchall()
            results.extend([r[0] for r in rows])
            conn.close()
        except Exception as e:
            pass
    
    elapsed = time.time() - start
    return results[:top_k], elapsed

def test_obsidian_search(query: str, top_k: int = 5) -> Tuple[List[str], float]:
    """测试Obsidian搜索性能"""
    start = time.time()
    results = []
    
    # 递归搜索所有.md文件
    for root, dirs, files in os.walk(OBSIDIAN_DIR):
        for f in files:
            if not f.endswith('.md'):
                continue
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                    if query in content:
                        results.append(filepath)
                        if len(results) >= top_k:
                            break
            except:
                pass
        if len(results) >= top_k:
            break
    
    elapsed = time.time() - start
    return results, elapsed

def main():
    """主测试函数"""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    test_queries = [
        'RPS',
        '尾盘',
        'Manim',
        'TTS',
        '热点',
    ]
    
    print("="*60)
    print("知识检索性能测试")
    print("时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*60)
    print()
    
    results_summary = []
    
    for query in test_queries:
        print(f"查询: {query}")
        
        # 测试Supermemory
        sm_results, sm_time = test_supermemory_search(query)
        print(f"  Supermemory: {len(sm_results)} results, {sm_time*1000:.1f}ms")
        
        # 测试Obsidian
        obs_results, obs_time = test_obsidian_search(query)
        print(f"  Obsidian: {len(obs_results)} results, {obs_time*1000:.1f}ms")
        
        results_summary.append({
            'query': query,
            'sm_count': len(sm_results),
            'sm_time': sm_time,
            'obs_count': len(obs_results),
            'obs_time': obs_time,
        })
        print()
    
    # 生成报告
    report_path = os.path.join(LOG_DIR, f'search_perf_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 知识检索性能报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 测试结果\n\n")
        f.write("| 查询 | Supermemory结果 | Supermemory耗时 | Obsidian结果 | Obsidian耗时 |\n")
        f.write("|------|----------------|----------------|-------------|-------------|\n")
        for r in results_summary:
            f.write(f"| {r['query']} | {r['sm_count']} | {r['sm_time']*1000:.1f}ms | {r['obs_count']} | {r['obs_time']*1000:.1f}ms |\n")
        
        f.write("\n## 分析\n\n")
        avg_sm = sum(r['sm_time'] for r in results_summary) / len(results_summary)
        avg_obs = sum(r['obs_time'] for r in results_summary) / len(results_summary)
        f.write(f"- Supermemory平均耗时: {avg_sm*1000:.1f}ms\n")
        f.write(f"- Obsidian平均耗时: {avg_obs*1000:.1f}ms\n")
        f.write(f"- 建议: {'使用Supermemory' if avg_sm < avg_obs else '使用Obsidian'}\n")
    
    print(f"报告已保存: {report_path}")

if __name__ == '__main__':
    main()
