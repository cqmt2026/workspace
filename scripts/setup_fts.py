#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
setup_fts.py - 为Supermemory建立FTS5全文索引
"""

import os
import sqlite3

SM_DIR = r"C:\Users\Administrator\.openclaw\workspace\memory\supermemory_db"

def setup_fts():
    created = 0
    for db_file in os.listdir(SM_DIR):
        if not db_file.endswith('.db'):
            continue
        db_path = os.path.join(SM_DIR, db_file)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 获取所有表
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall()]
        
        for table in tables:
            if '_fts' in table:
                continue
            
            # 检查是否有content列
            try:
                c.execute(f"PRAGMA table_info([{table}])")
                cols = [r[1] for r in c.fetchall()]
                if 'content' not in cols:
                    continue
            except:
                continue
            
            # 检查数据量
            c.execute(f"SELECT COUNT(*) FROM [{table}]")
            count = c.fetchone()[0]
            if count == 0:
                continue
            
            fts_name = table + '_fts'
            
            # 检查是否已存在
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (fts_name,))
            if c.fetchone():
                print(f"  {db_file}/{table}: FTS已存在")
                continue
            
            # 创建FTS表
            try:
                c.execute(f"CREATE VIRTUAL TABLE [{fts_name}] USING fts5(content, tokenize='unicode61')")
                c.execute(f"INSERT INTO [{fts_name}] SELECT content FROM [{table}]")
                conn.commit()
                created += 1
                print(f"  {db_file}/{table}: 已创建FTS ({count} rows)")
            except Exception as e:
                print(f"  {db_file}/{table}: ERROR - {e}")
        
        conn.close()
    
    print(f"\n总共创建: {created} 个FTS表")

if __name__ == "__main__":
    setup_fts()
