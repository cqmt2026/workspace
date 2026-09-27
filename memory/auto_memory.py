# -*- coding: utf-8 -*-
"""
Supermemory 自动启用脚本
本地版本，无需 API
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / '.supermemory' / 'memory.db'

def init_db():
    """初始化数据库"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            category TEXT,
            session_id TEXT,
            agent_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON memories(category)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON memories(created_at)')
    
    # 添加缺失的列
    try:
        conn.execute('ALTER TABLE memories ADD COLUMN entities TEXT')
    except:
        pass
    try:
        conn.execute('ALTER TABLE memories ADD COLUMN agent_id TEXT')
    except:
        pass
    
    conn.commit()
    conn.close()
    print("[OK] 数据库已初始化")

def save_memory(text, category="general", session_id=None, agent_id=None):
    """自动保存记忆"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO memories (text, category, session_id, agent_id) VALUES (?, ?, ?, ?)",
        (text, category, session_id, agent_id)
    )
    conn.commit()
    conn.close()
    print(f"[OK] 记忆已保存：{text[:50]}...")

def search_memory(query, category=None, top_k=10):
    """搜索记忆"""
    conn = sqlite3.connect(str(DB_PATH))
    if category:
        results = conn.execute(
            "SELECT * FROM memories WHERE text LIKE ? AND category = ? ORDER BY created_at DESC LIMIT ?",
            (f'%{query}%', category, top_k)
        ).fetchall()
    else:
        results = conn.execute(
            "SELECT * FROM memories WHERE text LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f'%{query}%', top_k)
        ).fetchall()
    conn.close()
    return results

def get_entity_profile(entity_name):
    """获取实体档案"""
    conn = sqlite3.connect(str(DB_PATH))
    results = conn.execute(
        "SELECT * FROM memories WHERE entities LIKE ? ORDER BY created_at",
        (f'%{entity_name}%',)
    ).fetchall()
    conn.close()
    return results

def auto_ingest_chapter(chapter_num, content):
    """自动提取章节事实"""
    # 提取基本信息
    save_memory(
        f"第{chapter_num}章：{content[:100]}...",
        category="chapter",
        session_id="novel",
        agent_id="novel-agent"
    )
    print(f"[OK] 第{chapter_num}章已存储")

def auto_inject_context(query):
    """自动注入上下文"""
    results = search_memory(query, top_k=5)
    if results:
        context = "\n".join([r[1] for r in results])
        print(f"[OK] 已注入上下文：{len(results)}条记忆")
        return context
    else:
        print("[WARN] 未找到相关记忆")
        return None

# 初始化
init_db()

if __name__ == '__main__':
    # 测试
    print("=" * 60)
    print("Supermemory 自动启用测试")
    print("=" * 60)
    
    # 测试保存
    save_memory("测试记忆", category="test")
    
    # 测试搜索
    results = search_memory("测试")
    print(f"搜索结果：{len(results)}条")
    
    # 测试章节存储
    auto_ingest_chapter(51, "这是第 51 章的内容...")
    
    # 测试上下文注入
    context = auto_inject_context("小说")
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
