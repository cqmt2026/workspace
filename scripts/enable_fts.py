#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
enable_fts.py - 为Supermemory启用全文搜索(FTS5)

功能：
1. 为每个memory表创建FTS5虚拟表
2. 同步现有数据到FTS表
3. 提供更快的全文检索能力

用法：
    python enable_fts.py [--db supermemory.db] [--rebuild]
"""

import os
import sys
import argparse
import sqlite3
import time
from pathlib import Path

# 路径配置
SM_DIR = r"C:\Users\Administrator\.openclaw\workspace\memory\supermemory_db"

def enable_fts_for_db(db_path: str, rebuild: bool = False):
    """为单个数据库启用FTS"""
    if not os.path.exists(db_path):
        print(f"  跳过: {db_path} 不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查是否已有FTS表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'memory_fts%'")
    existing_fts = [r[0] for r in cursor.fetchall()]
    
    if existing_fts and not rebuild:
        print(f"  已存在FTS表: {existing_fts[0]}，使用--rebuild强制重建")
        conn.close()
        return
    
    # 获取实际表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    
    # 找memory相关表
    memory_tables = [t for t in tables if 'memory' in t.lower()]
    if not memory_tables:
        print(f"  无memory表: {os.path.basename(db_path)}")
        conn.close()
        return
    
    table_name = memory_tables[0]
    fts_name = f"{table_name}_fts"
    
    print(f"  处理: {table_name} -> {fts_name}")
    
    # 删除旧的FTS表（如果重建）
    if rebuild and fts_name in existing_fts:
        cursor.execute(f"DROP TABLE IF EXISTS {fts_name}")
        conn.commit()
    
    # 创建FTS5表
    try:
        cursor.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {fts_name} USING fts5(
                content,
                content_rowid='rowid',
                tokenize='unicode61'
            )
        """)
        
        # 检查是否需要导入数据
        cursor.execute(f"SELECT COUNT(*) FROM {fts_name}")
        fts_count = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]
        
        if fts_count == 0 and total_count > 0:
            print(f"    导入 {total_count} 条记录...")
            cursor.execute(f"INSERT INTO {fts_name} SELECT * FROM {table_name}")
            conn.commit()
            print(f"    导入完成")
        elif fts_count == total_count:
            print(f"    数据已同步 ({fts_count}条)")
        else:
            print(f"    数据不一致: FTS={fts_count}, 实际={total_count}")
        
        # 创建触发器自动同步
        cursor.execute(f"""
            CREATE TRIGGER IF NOT EXISTS {table_name}_ai AFTER INSERT ON {table_name}
            BEGIN
                INSERT INTO {fts_name}(rowid, content) VALUES (new.rowid, new.content);
            END
        """)
        cursor.execute(f"""
            CREATE TRIGGER IF NOT EXISTS {table_name}_ad AFTER DELETE ON {table_name}
            BEGIN
                INSERT INTO {fts_name}({fts_name}, rowid, content) VALUES('delete', old.rowid, old.content);
            END
        """)
        cursor.execute(f"""
            CREATE TRIGGER IF NOT EXISTS {table_name}_au AFTER UPDATE ON {table_name}
            BEGIN
                INSERT INTO {fts_name}({fts_name}, rowid, content) VALUES('delete', old.rowid, old.content);
                INSERT INTO {fts_name}(rowid, content) VALUES (new.rowid, new.content);
            END
        """)
        conn.commit()
        print(f"    触发器已创建")
        
    except Exception as e:
        print(f"    错误: {e}")
        conn.rollback()
    
    conn.close()

def search_fts(db_path: str, query: str, top_k: int = 5):
    """使用FTS搜索"""
    if not os.path.exists(db_path):
        return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 找FTS表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'")
    fts_tables = [r[0] for r in cursor.fetchall()]
    
    if not fts_tables:
        conn.close()
        return []
    
    fts_table = fts_tables[0]
    
    try:
        cursor.execute(f"""
            SELECT content, rank FROM {fts_table} 
            WHERE {fts_table} MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, top_k))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        conn.close()
        return []

def main():
    parser = argparse.ArgumentParser(description="为Supermemory启用FTS全文搜索")
    parser.add_argument("--rebuild", action="store_true", help="重建所有FTS索引")
    parser.add_argument("--search", type=str, help="测试搜索")
    parser.add_argument("--top-k", type=int, default=5, help="返回结果数")
    args = parser.parse_args()
    
    print("="*60)
    print("Supermemory FTS启用工具")
    print("="*60)
    
    if not os.path.exists(SM_DIR):
        print(f"目录不存在: {SM_DIR}")
        return
    
    # 处理所有数据库
    dbs = [f for f in os.listdir(SM_DIR) if f.endswith('.db')]
    print(f"找到 {len(dbs)} 个数据库")
    
    for db in dbs:
        db_path = os.path.join(SM_DIR, db)
        enable_fts_for_db(db_path, args.rebuild)
    
    # 测试搜索
    if args.search:
        print()
        print(f"测试搜索: '{args.search}'")
        for db in dbs:
            db_path = os.path.join(SM_DIR, db)
            results = search_fts(db_path, args.search, args.top_k)
            if results:
                print(f"  {db}: {len(results)} results")
                for content, rank in results[:3]:
                    print(f"    - {content[:60]}...")

if __name__ == "__main__":
    main()
