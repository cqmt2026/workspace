#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fast_search.py - 快速检索工具

功能：
1. 优先使用FTS索引
2. 降级到LIKE查询
3. 支持多数据库联合搜索
4. 结果缓存

用法：
    python fast_search.py "RPS选股" --top 10
    python fast_search.py "低空经济" --source obsidian
"""

import os
import sys
import json
import time
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 路径配置
BASE = Path(r"C:\Users\Administrator\.openclaw\workspace")
SM_DIR = BASE / "memory" / "supermemory_db"
OBSIDIAN_DIR = Path(r"F:\Obsidian\Jarvis")
CACHE_DIR = BASE / "memory" / "search_cache"

class FastSearch:
    """快速搜索引擎"""
    
    def __init__(self):
        self.sm_dbs = {}
        self._load_dbs()
    
    def _load_dbs(self):
        """加载Supermemory数据库"""
        if not SM_DIR.exists():
            return
        for db_file in SM_DIR.glob("*.db"):
            conn = sqlite3.connect(str(db_file))
            self.sm_dbs[db_file.name] = conn
    
    def search_supermemory(self, query: str, top_k: int = 10) -> list:
        """搜索Supermemory"""
        results = []
        query_time = time.time()
        
        for db_name, conn in self.sm_dbs.items():
            cursor = conn.cursor()
            
            # 先尝试FTS
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'")
            fts_tables = [r[0] for r in cursor.fetchall()]
            
            if fts_tables:
                try:
                    cursor.execute(
                        f"SELECT content, rank, rowid FROM [{fts_tables[0]}] WHERE [{fts_tables[0]}] MATCH ? LIMIT ?",
                        (query, top_k)
                    )
                    for content, rank, rowid in cursor.fetchall():
                        results.append({
                            "source": f"supermemory://{db_name}",
                            "content": content,
                            "score": 1.0 - rank,  # 转换rank为相似度
                            "method": "fts"
                        })
                    if len(results) >= top_k:
                        break
                except:
                    pass
            
            # 降级到LIKE
            if len(results) < top_k:
                try:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [r[0] for r in cursor.fetchall()]
                    mem_tables = [t for t in tables if 'memory' in t.lower()]
                    if mem_tables:
                        cursor.execute(
                            f"SELECT content FROM [{mem_tables[0]}] WHERE content LIKE '%{query}%' LIMIT ?",
                            (top_k - len(results),)
                        )
                        for (content,) in cursor.fetchall():
                            results.append({
                                "source": f"supermemory://{db_name}",
                                "content": content,
                                "score": 0.5,
                                "method": "like"
                            })
                except:
                    pass
        
        elapsed = time.time() - query_time
        return results, elapsed
    
    def search_obsidian(self, query: str, top_k: int = 10) -> list:
        """搜索Obsidian"""
        if not OBSIDIAN_DIR.exists():
            return [], 0
        
        results = []
        start = time.time()
        
        for root, dirs, files in os.walk(str(OBSIDIAN_DIR)):
            # 跳过隐藏文件
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for f in files:
                if not f.endswith('.md'):
                    continue
                
                fp = Path(root) / f
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                        content = fh.read(3000)
                        if query in content:
                            results.append({
                                "source": f"obsidian://{fp.relative_to(OBSIDIAN_DIR)}",
                                "content": content,
                                "score": 0.8,
                                "method": "file_scan"
                            })
                            if len(results) >= top_k:
                                break
                except:
                    pass
            if len(results) >= top_k:
                break
        
        elapsed = time.time() - start
        return results, elapsed
    
    def search(self, query: str, top_k: int = 10, sources: list = None) -> dict:
        """统一搜索接口"""
        if sources is None:
            sources = ["supermemory", "obsidian"]
        
        all_results = []
        methods = {}
        
        if "supermemory" in sources:
            sm_results, sm_time = self.search_supermemory(query, top_k)
            all_results.extend(sm_results)
            methods["supermemory"] = {"time": sm_time, "count": len(sm_results)}
        
        if "obsidian" in sources:
            obs_results, obs_time = self.search_obsidian(query, top_k)
            all_results.extend(obs_results)
            methods["obsidian"] = {"time": obs_time, "count": len(obs_results)}
        
        # 按分数排序
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "query": query,
            "results": all_results[:top_k],
            "methods": methods,
            "total": len(all_results),
            "timestamp": datetime.now().isoformat()
        }

def main():
    parser = argparse.ArgumentParser(description="快速检索工具")
    parser.add_argument("query", help="搜索查询")
    parser.add_argument("--top-k", type=int, default=10, help="返回结果数")
    parser.add_argument("--source", choices=["all", "supermemory", "obsidian"], default="all", help="搜索来源")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    args = parser.parse_args()
    
    sources = None
    if args.source != "all":
        sources = [args.source]
    
    searcher = FastSearch()
    result = searcher.search(args.query, args.top_k, sources)
    
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"搜索: {result['query']}")
        print(f"耗时: {sum(m['time'] for m in result['methods'].values())*1000:.1f}ms")
        print(f"结果: {result['total']}条")
        print()
        for i, r in enumerate(result['results'][:args.top_k], 1):
            src = str(r['source'])[:80]
            content = str(r['content'])[:100]
            print(str(i) + '. [' + r['method'] + '] ' + src)
            print('   ' + content)
            print()

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
