# -*- coding: utf-8 -*-
"""
Memory Tools v3.1
多DB分库版本 — 每个子系统独立DB，彻底解决领域污染
"""

import json
import logging
import os
import sqlite3
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# 分库映射（本地路径，不依赖外部服务）
DB_DIR = r"C:\Users\Administrator\.openclaw\workspace\memory\supermemory_db"
DOMAIN_DB = {
    'novel':      os.path.join(DB_DIR, 'memory_novel.db'),
    'investment': os.path.join(DB_DIR, 'memory_investment.db'),
    'social':     os.path.join(DB_DIR, 'memory_social.db'),
    'math':       os.path.join(DB_DIR, 'memory_math.db'),
    'system':     os.path.join(DB_DIR, 'memory_system.db'),
}
GLOBAL_DB = os.path.join(DB_DIR, 'memory.db')


def _ensure_db(path: str, domain: str = None):
    """确保DB文件存在且建好表"""
    exists = os.path.exists(path)
    conn = sqlite3.connect(path)
    if not exists:
        conn.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS source_chunks (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                session_key TEXT,
                agent_id TEXT,
                document_date TEXT
            );
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                confidence REAL DEFAULT 1.0,
                document_date TEXT,
                source_session TEXT,
                source_agent TEXT,
                source_chunk_id TEXT,
                embedding BLOB,
                entities TEXT,
                version INTEGER DEFAULT 1,
                is_current INTEGER DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_memories_current ON memories(is_current);
            CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
        """)
    # 投资库：确保 content 上有索引（LIKE 搜索用）
    if domain == 'investment':
        try:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memories_content ON memories(content)"
            )
        except Exception as e:
            logger.warning(f"投资库索引创建失败: {e}")
    conn.close()


# 启动时确保所有分库存在
for domain, path in DOMAIN_DB.items():
    _ensure_db(path, domain=domain)


# ============================================================
# DB 工具
# ============================================================

def _get_conn(db_path: str):
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# MemoryTools 统一接口
# ============================================================

class MemoryTools:
    """记忆工具 v3.1 — 多DB分库（LIKE搜索，不依赖外部服务）"""

    def __init__(self):
        pass

    def _get_db_path(self, domain: str = None) -> str:
        if domain and domain in DOMAIN_DB:
            return DOMAIN_DB[domain]
        return GLOBAL_DB

    # --------------------------------------------------
    # 状态
    # --------------------------------------------------

    def get_status(self, domain: str = None) -> Dict[str, Any]:
        path = self._get_db_path(domain)
        try:
            conn = _get_conn(path)
            total = conn.execute(
                "SELECT count(*) as c FROM memories WHERE is_current = 1"
            ).fetchone()["c"]
            with_emb = conn.execute(
                "SELECT count(*) as c FROM memories WHERE is_current = 1 AND embedding IS NOT NULL"
            ).fetchone()["c"]
            conn.close()
            return {
                "domain": domain or "global",
                "db": os.path.basename(path),
                "memories": total,
                "embedded": with_emb,
                "status": "ready",
            }
        except Exception as e:
            return {"domain": domain or "global", "status": "error", "error": str(e)}

    def get_all_status(self) -> Dict[str, Any]:
        result = {}
        result['global'] = self.get_status()
        for domain in DOMAIN_DB:
            result[domain] = self.get_status(domain)
        return result

    # --------------------------------------------------
    # 保存记忆
    # --------------------------------------------------

    def save_memory(
        self,
        text: str,
        category: str = "general",
        entities: List[str] = None,
        session_id: str = None,
        agent_id: str = None,
        source: str = None,
        domain: str = None,
    ) -> Dict[str, Any]:
        """
        保存记忆到指定领域DB（domain=None 则写入全局DB）
        """
        db_path = self._get_db_path(domain)
        _ensure_db(db_path, domain=domain)
        conn = _get_conn(db_path)
        try:
            existing = conn.execute(
                "SELECT id FROM memories WHERE content = ? AND is_current = 1 LIMIT 1",
                (text,),
            ).fetchone()
            if existing:
                return {"success": True, "memory_id": existing["id"], "note": "duplicate"}

            chunk_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO source_chunks (id, content, session_key, agent_id, document_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (chunk_id, text, session_id or "direct", agent_id or "direct",
                 datetime.now().strftime("%Y-%m-%d")),
            )

            mem_id = str(uuid.uuid4())
            entities_str = ",".join(entities) if entities else None
            cur = conn.execute(
                """INSERT INTO memories
                   (id, content, category, confidence, document_date,
                    source_session, source_agent, source_chunk_id, entities,
                    version, is_current)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)""",
                (mem_id, text, category, 1.0, datetime.now().strftime("%Y-%m-%d"),
                 session_id or "direct", agent_id or "direct", chunk_id, entities_str),
            )
            conn.commit()
            return {"success": True, "memory_id": mem_id, "domain": domain or "global"}

        except Exception as e:
            conn.rollback()
            logger.error(f"save_memory 失败: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    # --------------------------------------------------
    # 语义搜索（可跨域搜索）
    # --------------------------------------------------

    def search_memory(
        self,
        query: str,
        category: str = None,
        top_k: int = 10,
        threshold: float = 0.0,
        domain: str = None,
    ) -> Dict[str, Any]:
        """
        搜索记忆。domain=None 则搜索全局DB，domain='*' 则搜索所有分库并合并
        使用 LIKE 关键词搜索（不依赖外部服务）
        """
        if domain == '*':
            # 跨域搜索：搜所有分库 + 全局库，合并排序
            all_results = []
            for d in list(DOMAIN_DB.keys()) + [None]:
                r = self.search_memory(query, category=category, top_k=top_k, threshold=threshold, domain=d)
                for m in r['results']:
                    m['_domain'] = d or 'global'
                    all_results.append(m)
            all_results.sort(key=lambda x: x['score'], reverse=True)
            return {
                "success": True,
                "query": query,
                "results": all_results[:top_k],
                "count": len(all_results),
            }

        db_path = self._get_db_path(domain)
        conn = _get_conn(db_path)
        try:
            # 全局 LIKE 关键词搜索（所有域统一使用）
            import re
            q = query.strip()
            if not q:
                return {"success": True, "query": query, "results": [], "count": 0}

            keywords = [w for w in re.split(r'\s+', q) if len(w) >= 2][:10]
            if not keywords:
                keywords = [q[:2]] if len(q) >= 2 else [q]

            where_parts = ["m.is_current = 1"]
            params = []
            if category:
                where_parts.append("m.category = ?")
                params.append(category)

            like_clauses = []
            for kw in keywords:
                like_clauses.append("m.content LIKE ?")
                params.append(f'%{kw}%')
            where_parts.append('(' + ' OR '.join(like_clauses) + ')')

            sql = (
                "SELECT m.id, m.content, m.category, m.confidence, m.document_date "
                "FROM memories m WHERE " + ' AND '.join(where_parts) + " LIMIT ?"
            )
            params.append(top_k)

            rows = conn.execute(sql, params).fetchall()

            results = []
            for r in rows:
                results.append({
                    "id": r["id"],
                    "text": r["content"],
                    "category": r["category"],
                    "score": 1.0,
                    "created_at": r["document_date"],
                    "domain": domain or "global",
                })
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
            }
        finally:
            conn.close()

    # --------------------------------------------------
    # 兼容旧接口
    # --------------------------------------------------

    def recall(self, context: str, top_k: int = 5, domain: str = None) -> Dict[str, Any]:
        return self.search_memory(context, top_k=top_k, domain=domain)

    def get_entity_profile(self, entity_name: str, domain: str = None) -> Dict[str, Any]:
        r = self.search_memory(entity_name, top_k=20, domain=domain)
        return {"success": True, "name": entity_name, "memories": r["results"], "profile": {}}

    def get_entity_history(self, entity_name: str, domain: str = None) -> Dict[str, Any]:
        r = self.search_memory(entity_name, top_k=50, domain=domain)
        return {"success": True, "name": entity_name,
                "history": sorted(r["results"], key=lambda x: x.get("created_at", ""))}

    def get_stats(self) -> Dict[str, Any]:
        return self.get_all_status()


# ============================================================
# 降级搜索（向量搜索失败时的 LIKE 回退）
# ============================================================

def _like_search_fallback(query, conn, category, top_k, domain):
    """向量搜索失败时，降级为 LIKE 关键词搜索。"""
    import re
    q = query.strip()
    if not q:
        return {"success": True, "query": query, "results": [], "count": 0}

    keywords = [w for w in re.split(r'\s+', q) if len(w) >= 2][:10]
    if not keywords:
        keywords = [q[:2]] if len(q) >= 2 else [q]

    where_parts = ["m.is_current = 1"]
    params = []
    if category:
        where_parts.append("m.category = ?")
        params.append(category)

    like_clauses = []
    for kw in keywords:
        like_clauses.append("m.content LIKE ?")
        params.append(f'%{kw}%')
    where_parts.append('(' + ' OR '.join(like_clauses) + ')')

    sql = (
        "SELECT m.id, m.content, m.category, m.confidence, m.document_date "
        "FROM memories m WHERE " + ' AND '.join(where_parts) + " LIMIT ?"
    )
    params.append(top_k)

    try:
        rows = conn.execute(sql, params).fetchall()
    except Exception as e:
        logger.error(f"LIKE 降级搜索也失败: {e}")
        return {"success": True, "query": query, "results": [], "count": 0, "note": "fallback_failed"}

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "text": r["content"],
            "category": r["category"],
            "score": 0.5,
            "created_at": r["document_date"],
            "domain": domain or "global",
            "fallback": True,
        })
    return {
        "success": True,
        "query": query,
        "results": results,
        "count": len(results),
        "note": "vector_search_fallback_to_like",
    }


# ============================================================
# 全局单例
# ============================================================

_INSTANCE: Optional[MemoryTools] = None
def get_memory_tools() -> MemoryTools:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = MemoryTools()
    return _INSTANCE


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mt = MemoryTools()

    print("=== 分库状态 ===")
    for d, s in mt.get_all_status().items():
        print(f"  {d}: {s['memories']}条")

    print()
    print("=== 写入测试 ===")
    r = mt.save_memory("陆鸣在天台上发现裂缝", category="plot", domain="novel")
    print(f"  小说库: {r.get('domain')} id={r.get('memory_id','')[:8]}")

    r = mt.save_memory("涨停策略：放量+MACD金叉", category="strategy", domain="investment")
    print(f"  投资库: {r.get('domain')} id={r.get('memory_id','')[:8]}")

    print()
    print("=== 域内搜索（无污染）===")
    r = mt.search_memory("陆鸣", top_k=5, domain="novel")
    print(f"  小说库搜'陆鸣': {r['count']}条")
    for m in r['results']:
        print(f"    [{m['score']:.4f}] {m['text'][:40]}")

    r = mt.search_memory("陆鸣", top_k=5, domain="investment")
    print(f"  投资库搜'陆鸣': {r['count']}条")

    print()
    print("=== 跨域搜索 ===")
    r = mt.search_memory("陆鸣", top_k=5, domain="*")
    print(f"  跨域搜'陆鸣': {r['count']}条")
    for m in r['results']:
        print(f"    [{m['_domain']}] [{m['score']:.4f}] {m['text'][:40]}")