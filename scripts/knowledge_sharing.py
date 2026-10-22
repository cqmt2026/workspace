#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
knowledge_sharing.py - 跨系统知识共享工具（领域隔离版）

功能：
1. 扫描各子系统知识库（只读索引）
2. 建立统一索引（标注领域）
3. 支持跨领域搜索（返回结果标注来源）
4. 处理一词多义问题

用法：
    python knowledge_sharing.py --scan              # 重建索引
    python knowledge_sharing.py --search "热点"     # 搜索（返回所有领域）
    python knowledge_sharing.py --search "热点" --domain investment  # 限定领域
    python knowledge_sharing.py --domains          # 查看领域列表
"""

import os
import sys
import json
import hashlib
import datetime
from pathlib import Path
from collections import defaultdict

BASE = Path(r"C:\Users\Administrator\.openclaw")
INDEX_FILE = BASE / "workspace" / "memory" / "knowledge_index.json"

# 领域词典：每个领域的专业术语
DOMAIN_DICTIONARY = {
    "investment": {
        "name": "投资系统",
        "keywords": ["RPS", "策略", "选股", "量化", "回测", "热点", "主线", "数据", "涨停", "板块"],
        "paths": [BASE / "workspace-investment" / "memory"]
    },
    "novel": {
        "name": "小说系统",
        "keywords": ["创作", "章节", "人物", "大纲", "热点", "主线", "数据", "读者", "订阅"],
        "paths": [BASE / "workspace-novel" / "memory"]
    },
    "social": {
        "name": "自媒体系统",
        "keywords": ["热点", "视频", "发布", "运营", "策略", "数据", "流量", "爆款"],
        "paths": [BASE / "workspace-social" / "memory"]
    },
    "math": {
        "name": "数学动画",
        "keywords": ["Manim", "动画", "数学", "可视化", "数据", "脚本", "渲染"],
        "paths": [BASE / "workspace-math" / "memory"]
    },
    "maphot": {
        "name": "地图热点",
        "keywords": ["地图", "热点", "地理", "数据", "城市", "人口", "经济"],
        "paths": [BASE / "workspace-maphot" / "memory"]
    },
    "weixin": {
        "name": "微信小程序",
        "keywords": ["小程序", "微信", "开发", "数据", "接口"],
        "paths": [BASE / "workspace-weixin" / "memory"]
    }
}

def scan_knowledge():
    """扫描所有领域知识（只读索引）"""
    index = {
        "timestamp": datetime.datetime.now().isoformat(),
        "domains": {},
        "terms": defaultdict(list),  # 术语 -> [{domain, path, content_hash}]
        "cross_domain": []  # 跨领域关联
    }
    
    for domain, config in DOMAIN_DICTIONARY.items():
        domain_data = {
            "name": config["name"],
            "keywords": config["keywords"],
            "file_count": 0,
            "files": []
        }
        
        for path in config["paths"]:
            if not path.exists():
                continue
            
            md_files = list(path.glob("*.md"))
            domain_data["file_count"] += len(md_files)
            
            for f in md_files:
                try:
                    with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
                        content = fh.read(3000)  # 读取前3000字符
                    
                    # 计算内容哈希（用于去重）
                    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
                    
                    # 提取领域关键词
                    file_terms = []
                    for kw in config["keywords"]:
                        if kw in content:
                            file_terms.append(kw)
                    
                    file_info = {
                        "name": f.name,
                        "path": str(f.relative_to(BASE)),
                        "size": f.stat().st_size,
                        "modified": datetime.datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                        "terms": file_terms,
                        "hash": content_hash
                    }
                    
                    domain_data["files"].append(file_info)
                    
                    # 更新全局术语索引
                    for term in file_terms:
                        index["terms"][term].append({
                            "domain": domain,
                            "domain_name": config["name"],
                            "path": str(f.relative_to(BASE)),
                            "hash": content_hash
                        })
                        
                except Exception as e:
                    print(f"  错误 [{domain}] {f.name}: {e}")
        
        index["domains"][domain] = domain_data
    
    # 检测跨领域关联（相同术语出现在多个领域）
    for term, occurrences in index["terms"].items():
        domains = list(set([o["domain"] for o in occurrences]))
        if len(domains) > 1:
            index["cross_domain"].append({
                "term": term,
                "domains": domains,
                "count": len(occurrences)
            })
    
    # 保存索引
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    return index

def search_knowledge(query, domain=None, top_k=10):
    """搜索知识（带领域标注）"""
    if not INDEX_FILE.exists():
        return {"error": "索引不存在，请先执行--scan"}
    
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    results = []
    
    # 精确匹配术语
    if query in index["terms"]:
        for occurrence in index["terms"][query]:
            if domain and occurrence["domain"] != domain:
                continue
            results.append({
                "type": "term_match",
                "term": query,
                "domain": occurrence["domain"],
                "domain_name": occurrence["domain_name"],
                "path": occurrence["path"],
                "relevance": 1.0
            })
    
    # 文件名模糊匹配
    for dom_name, dom_data in index["domains"].items():
        if domain and dom_name != domain:
            continue
        for f in dom_data["files"]:
            if query.lower() in f["name"].lower():
                results.append({
                    "type": "filename_match",
                    "term": query,
                    "domain": dom_name,
                    "domain_name": dom_data["name"],
                    "path": f["path"],
                    "relevance": 0.7
                })
    
    # 按相关性排序
    results.sort(key=lambda x: x["relevance"], reverse=True)
    
    return {
        "query": query,
        "domain_filter": domain,
        "total": len(results),
        "results": results[:top_k]
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='跨系统知识共享（领域隔离版）')
    parser.add_argument('--scan', action='store_true', help='重建索引')
    parser.add_argument('--search', type=str, help='搜索知识')
    parser.add_argument('--domain', type=str, choices=list(DOMAIN_DICTIONARY.keys()), 
                       help='限定领域')
    parser.add_argument('--domains', action='store_true', help='显示领域列表')
    parser.add_argument('--cross-domain', action='store_true', help='显示跨领域术语')
    parser.add_argument('--top-k', type=int, default=10, help='返回结果数')
    args = parser.parse_args()
    
    if args.scan:
        print("扫描知识库（领域隔离模式）...")
        index = scan_knowledge()
        print(f"完成: {len(index['domains'])}个领域, {sum(d['file_count'] for d in index['domains'].values())}个文件")
        print(f"跨领域术语: {len(index['cross_domain'])}个")
        
    elif args.search:
        result = search_knowledge(args.search, args.domain, args.top_k)
        if "error" in result:
            print(result["error"])
            return
        
        print(f"搜索: '{result['query']}'" + (f" [领域: {args.domain}]" if args.domain else ""))
        print(f"结果: {result['total']}条")
        print()
        
        for i, r in enumerate(result["results"], 1):
            domain_emoji = {"investment": "[投资]", "novel": "[小说]", "social": "[自媒体]", 
                           "math": "[数学]", "maphot": "[地图]", "weixin": "[小程序]"}
            tag = domain_emoji.get(r["domain"], "[其他]")
            print(str(i) + '. ' + tag + ' ' + r['path'].split('/')[-1])
            print(f"   路径: {r['path']}")
            print()
            
    elif args.domains:
        print("=== 领域列表 ===")
        for domain, config in DOMAIN_DICTIONARY.items():
            print(f"  {domain}: {config['name']}")
            print(f"    关键词: {', '.join(config['keywords'][:5])}...")
        print()
        
    elif args.cross_domain:
        if not INDEX_FILE.exists():
            print("索引不存在，先执行--scan")
            return
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index = json.load(f)
        print("=== 跨领域术语（一词多义）===")
        for item in index["cross_domain"]:
            print(f"  '{item['term']}': {', '.join(item['domains'])} ({item['count']}个文件)")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
