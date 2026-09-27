# -*- coding: utf-8 -*-
"""
光伏获客系统 - 数据库层
"""
import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

# 路径设置 - 固定使用workspace-pv/data/pv.db
BASE = Path(__file__).parent.parent.parent
_DB_PATH = BASE / "data" / "pv.db"
DB_PATH = _DB_PATH

class PVDatabase:
    """光伏获客系统数据库"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self.conn = None
        self._connect()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur

    # ========== 热点话题 ==========
    def add_hot_topic(self, title: str, source: str, hot_score: int = 0,
                      pv_score: float = 0.0, pv_related: int = 0,
                      keywords: str = "", url: str = "", summary: str = "") -> int:
        cur = self.execute("""
            INSERT OR IGNORE INTO hot_topics
            (title, source, hot_score, pv_score, pv_related, keywords, url, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, source, hot_score, pv_score, pv_related, keywords, url, summary))
        self.conn.commit()
        return cur.lastrowid

    def get_latest_pv_topics(self, limit: int = 20) -> List[Dict]:
        cur = self.execute("""
            SELECT * FROM hot_topics
            WHERE pv_related = 1
            ORDER BY hot_score DESC, collected_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in cur.fetchall()]

    def get_today_pv_topics(self, limit: int = 20) -> List[Dict]:
        cur = self.execute("""
            SELECT * FROM hot_topics
            WHERE pv_related = 1
              AND date(collected_at) = date('now','localtime')
            ORDER BY hot_score DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in cur.fetchall()]

    # ========== 政策 ==========
    def add_policy(self, title: str, province: Optional[str], level: str = "national",
                   policy_type: str = "other", content: str = "", url: str = "",
                   source: str = "web") -> int:
        cur = self.execute("""
            INSERT OR IGNORE INTO policies
            (title, province, level, policy_type, content, url, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, province, level, policy_type, content, url, source))
        self.conn.commit()
        return cur.lastrowid

    def get_latest_policies(self, limit: int = 10) -> List[Dict]:
        cur = self.execute("SELECT * FROM policies ORDER BY collected_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

    # ========== 竞品 ==========
    def add_competitor(self, platform: str, account_name: str,
                       account_id: str = "", followers: int = 0) -> int:
        cur = self.execute("""
            INSERT OR IGNORE INTO competitors
            (platform, account_name, account_id, followers)
            VALUES (?, ?, ?, ?)
        """, (platform, account_name, account_id, followers))
        self.conn.commit()
        return cur.lastrowid

    def get_all_competitors(self) -> List[Dict]:
        cur = self.execute("SELECT * FROM competitors ORDER BY followers DESC")
        return [dict(r) for r in cur.fetchall()]

    # ========== 区域数据 ==========
    def add_region_data(self, province: str, city: Optional[str],
                        avg_sunshine: float = 0, residential_electricity: float = 0,
                        subsidy_local: float = 0, data_date: str = None) -> int:
        if data_date is None:
            data_date = datetime.now().strftime("%Y-%m-%d")
        cur = self.execute("""
            INSERT OR REPLACE INTO region_data
            (province, city, avg_sunshine, residential_electricity, subsidy_local, data_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (province, city, avg_sunshine, residential_electricity, subsidy_local, data_date))
        self.conn.commit()
        return cur.lastrowid

    def get_all_region_data(self) -> List[Dict]:
        cur = self.execute("SELECT * FROM region_data ORDER BY avg_sunshine DESC")
        return [dict(r) for r in cur.fetchall()]

    # ========== 系统日志 ==========
    def log_action(self, module: str, action: str, status: str = "ok", message: str = ""):
        self.execute("""
            INSERT INTO system_logs (module, action, status, message)
            VALUES (?, ?, ?, ?)
        """, (module, action, status, str(message)[:500]))
        self.conn.commit()

    # ========== 分析 ==========
    def get_pv_analysis(self, days: int = 7) -> Dict[str, Any]:
        result = {}
        cur = self.execute("""
            SELECT COUNT(*) as cnt FROM hot_topics
            WHERE pv_related = 1
              AND date(collected_at) = date('now','localtime')
        """)
        result["today_pv_topics"] = cur.fetchone()["cnt"]
        # 30天总量（用于弥补当日可能为0的情况）
        cur30 = self.execute("""
            SELECT COUNT(*) as cnt FROM hot_topics
            WHERE pv_related = 1
              AND collected_at >= datetime('now','localtime', '-30 days')
        """)
        result["total_pv_topics"] = cur30.fetchone()["cnt"]

        cur = self.execute("""
            SELECT date(collected_at) as d, COUNT(*) as cnt
            FROM hot_topics
            WHERE pv_related = 1 AND collected_at >= datetime('now', 'localtime', ?)
            GROUP BY d ORDER BY d
        """, (f"-{days} days",))
        result["trends"] = [dict(r) for r in cur.fetchall()]

        cur = self.execute("""
            SELECT source, COUNT(*) as cnt
            FROM hot_topics
            WHERE pv_related = 1 AND collected_at >= datetime('now', 'localtime', ?)
            GROUP BY source
        """, (f"-{days} days",))
        result["sources"] = {r["source"]: r["cnt"] for r in cur.fetchall()}

        cur = self.execute("""
            SELECT COUNT(*) as cnt FROM policies
            WHERE collected_at >= datetime('now', 'localtime', ?)
        """, (f"-{days} days",))
        result["policy_count"] = cur.fetchone()["cnt"]

        cur = self.execute("SELECT COUNT(*) as cnt FROM competitors")
        result["competitor_count"] = cur.fetchone()["cnt"]

        return result

    def save_content_item(self, content_id: str, channel: str, filepath: str = "", status: str = "draft",
                           tracking_id: str = None, geo_score: int = 0, **kwargs) -> int:
        """保存内容项到 content_items 表
        
        注意：update时不覆盖已有的非draft状态（如published），
        避免多渠道导出时后者覆盖前者的状态。
        """
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            cur = self.conn.cursor()
            cur.execute("""
                SELECT id, status FROM content_items WHERE content_id=?
            """, (content_id,))
            existing = cur.fetchone()
            if existing:
                # 保持已有状态：如果已经是published，不要回退到draft
                existing_status = existing['status'] if existing['status'] else 'draft'
                new_status = existing_status if existing_status == 'published' else status
                cur.execute("""
                    UPDATE content_items SET channel=?, status=?, published_at=?, tracking_id=?, geo_score=?
                    WHERE content_id=?
                """, (channel, new_status, now, tracking_id, geo_score, content_id))
            else:
                cur.execute("""
                    INSERT INTO content_items
                    (content_id, tracking_id, channel, status, published_at, geo_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (content_id, tracking_id, channel, status, now, geo_score))
            self.conn.commit()
            return cur.rowcount
        except Exception as e:
            self.log_action("database", "save_content_item", "error", str(e)[:500])
            return 0

    def close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def init_db(db_path: str = None):
    conn = sqlite3.connect(db_path or str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cur = conn.cursor()

    tables = {
        "hot_topics": """
            CREATE TABLE IF NOT EXISTS hot_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT,
                hot_score INTEGER DEFAULT 0,
                category TEXT,
                summary TEXT,
                keywords TEXT,
                pv_related INTEGER DEFAULT 0,
                pv_score REAL DEFAULT 0.0,
                collected_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(title, source)
            )""",
        "policies": """
            CREATE TABLE IF NOT EXISTS policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                province TEXT,
                level TEXT DEFAULT 'national',
                policy_type TEXT DEFAULT 'other',
                subsidy_amount REAL,
                content TEXT,
                url TEXT,
                source TEXT DEFAULT 'web',
                collected_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(title, province)
            )""",
        "competitors": """
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                account_name TEXT NOT NULL,
                account_id TEXT,
                followers INTEGER DEFAULT 0,
                avg_likes INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(platform, account_name)
            )""",
        "competitor_contents": """
            CREATE TABLE IF NOT EXISTS competitor_contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id INTEGER REFERENCES competitors(id),
                title TEXT NOT NULL,
                url TEXT,
                play_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                published_at TEXT,
                collected_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(competitor_id, title)
            )""",
        "pv_companies": """
            CREATE TABLE IF NOT EXISTS pv_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                province TEXT,
                city TEXT,
                business_type TEXT,
                scale TEXT,
                source TEXT,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(name, province)
            )""",
        "region_data": """
            CREATE TABLE IF NOT EXISTS region_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                province TEXT NOT NULL,
                city TEXT,
                avg_sunshine REAL,
                residential_electricity REAL,
                rural_household_ratio REAL,
                pv_installed_capacity REAL,
                subsidy_local REAL,
                data_date TEXT,
                collected_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(province, city, data_date)
            )""",
        "system_logs": """
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT DEFAULT 'ok',
                message TEXT,
                duration_ms INTEGER,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )""",
    }

    for name, ddl in tables.items():
        cur.execute(ddl)

    conn.commit()
    conn.close()
    return True


def init_business_tables(db_path: str = None):
    """初始化业务数据表（leads/content_items/campaigns/attribution）"""
    conn = sqlite3.connect(db_path or str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cur = conn.cursor()

    tables = {
        "leads": """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_channel TEXT,
                source_content_id TEXT,
                name TEXT,
                phone TEXT,
                level TEXT DEFAULT 'C',
                tags TEXT,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )""",
        "content_items": """
            CREATE TABLE IF NOT EXISTS content_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id TEXT UNIQUE,
                tracking_id TEXT,
                channel TEXT,
                status TEXT DEFAULT 'draft',
                plays INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                leads_generated INTEGER DEFAULT 0,
                published_at TEXT,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )""",
        "campaigns": """
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                channel TEXT,
                budget REAL DEFAULT 0,
                start_date TEXT,
                end_date TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )""",
        "attribution": """
            CREATE TABLE IF NOT EXISTS attribution (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id TEXT,
                channel TEXT,
                lead_id INTEGER,
                converted INTEGER DEFAULT 0,
                close_amount REAL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )""",
    }

    for name, ddl in tables.items():
        cur.execute(ddl)

    conn.commit()
    conn.close()
    return True
