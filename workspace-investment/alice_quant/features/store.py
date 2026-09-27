"""因子存储 - 内存缓存+SQLite持久化

存储结构：
  内存: {date: {code: {factor_name: value}}}
  SQLite: factors表 (date, code, factor_name, value, updated_at)

不再使用parquet按月分文件，改为：
  1. 内存LRU缓存（优先）
  2. SQLite持久化（持久）
  3. 批量读写
"""
import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict


class FactorStore:
    """因子存储"""

    def __init__(self, config=None):
        self._config = config
        # 内存缓存: {date: {code: {factor_name: value}}}
        self._cache: Dict[str, Dict[str, Dict[str, float]]] = {}
        # SQLite连接
        self._conn = None
        self._db_path = ''
        self._initialized = False

    def initialize(self):
        """初始化：连接SQLite并建表"""
        self._db_path = self._get_db_path()
        if not self._db_path:
            return

        try:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS factors (
                    date TEXT NOT NULL,
                    code TEXT NOT NULL,
                    factor_name TEXT NOT NULL,
                    value REAL,
                    updated_at TEXT DEFAULT (datetime('now')),
                    PRIMARY KEY (date, code, factor_name)
                )
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS ic_history (
                    date TEXT NOT NULL,
                    factor_name TEXT NOT NULL,
                    ic REAL,
                    p_value REAL,
                    n_stocks INTEGER,
                    updated_at TEXT DEFAULT (datetime('now')),
                    PRIMARY KEY (date, factor_name)
                )
            """)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS factor_status (
                    factor_name TEXT PRIMARY KEY,
                    category TEXT,
                    mean_ic REAL DEFAULT 0,
                    ic_ir REAL DEFAULT 0,
                    positive_ratio REAL DEFAULT 0,
                    n_days INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    last_updated TEXT DEFAULT (datetime('now'))
                )
            """)
            self._conn.commit()
            self._initialized = True
        except Exception:
            self._conn = None

    def save_factor(self, date: str, code: str, factor_name: str, value: float):
        """保存单个因子值"""
        # 内存缓存
        if date not in self._cache:
            self._cache[date] = {}
        if code not in self._cache[date]:
            self._cache[date][code] = {}
        self._cache[date][code][factor_name] = value

        # SQLite持久化
        if self._conn:
            try:
                self._conn.execute("""
                    INSERT OR REPLACE INTO factors (date, code, factor_name, value)
                    VALUES (?, ?, ?, ?)
                """, (date, code, factor_name, value))
                self._conn.commit()
            except Exception:
                pass

    def save_factors_batch(self, factors: Dict[str, Dict[str, Dict[str, float]]]):
        """批量保存因子

        Args:
            factors: {date: {code: {factor_name: value}}}
        """
        # 内存缓存
        for date, codes in factors.items():
            if date not in self._cache:
                self._cache[date] = {}
            for code, fvals in codes.items():
                if code not in self._cache[date]:
                    self._cache[date][code] = {}
                self._cache[date][code].update(fvals)

        # SQLite批量写入
        if self._conn:
            rows = []
            for date, codes in factors.items():
                for code, fvals in codes.items():
                    for fname, val in fvals.items():
                        rows.append((date, code, fname, val))
            if rows:
                try:
                    self._conn.executemany("""
                        INSERT OR REPLACE INTO factors (date, code, factor_name, value)
                        VALUES (?, ?, ?, ?)
                    """, rows)
                    self._conn.commit()
                except Exception:
                    pass

    def get_factor(self, code: str, factor_name: str, date: str) -> Optional[float]:
        """获取单个因子值

        优先从内存缓存读取。
        """
        # 内存缓存
        if date in self._cache and code in self._cache[date]:
            val = self._cache[date][code].get(factor_name)
            if val is not None:
                return val

        # SQLite
        if self._conn:
            try:
                cursor = self._conn.execute(
                    "SELECT value FROM factors WHERE date=? AND code=? AND factor_name=?",
                    (date, code, factor_name)
                )
                row = cursor.fetchone()
                if row:
                    return row[0]
            except Exception:
                pass
        return None

    def get_factors(self, codes: List[str], factor_names: List[str],
                    date: str) -> Dict[str, Dict[str, float]]:
        """批量获取因子

        Args:
            codes: 股票代码列表
            factor_names: 因子名称列表
            date: 日期

        Returns:
            {code: {factor_name: value}}
        """
        result: Dict[str, Dict[str, float]] = {}

        # 内存缓存
        if date in self._cache:
            for code in codes:
                if code in self._cache[date]:
                    cf = {n: self._cache[date][code][n]
                          for n in factor_names if n in self._cache[date][code]}
                    if cf:
                        result[code] = cf

        # SQLite补缺失
        missing_codes = [c for c in codes if c not in result]
        if missing_codes and self._conn:
            try:
                placeholders = ','.join(['?'] * len(missing_codes))
                f_placeholders = ','.join(['?'] * len(factor_names))
                cursor = self._conn.execute(f"""
                    SELECT code, factor_name, value FROM factors
                    WHERE date=? AND code IN ({placeholders}) AND factor_name IN ({f_placeholders})
                """, [date] + missing_codes + factor_names)
                for row in cursor.fetchall():
                    code, fname, val = row
                    if code not in result:
                        result[code] = {}
                    result[code][fname] = val
            except Exception:
                pass

        return result

    def get_date_range(self) -> tuple:
        """获取因子数据覆盖范围"""
        if self._conn:
            try:
                cursor = self._conn.execute(
                    "SELECT MIN(date), MAX(date), COUNT(DISTINCT code) FROM factors"
                )
                return cursor.fetchone()
            except Exception:
                pass
        return ('', '', 0)

    def save_ic(self, date: str, factor_name: str, ic: float,
                p_value: float, n_stocks: int):
        """保存IC记录"""
        if self._conn:
            try:
                self._conn.execute("""
                    INSERT OR REPLACE INTO ic_history
                    (date, factor_name, ic, p_value, n_stocks)
                    VALUES (?, ?, ?, ?, ?)
                """, (date, factor_name, ic, p_value, n_stocks))
                self._conn.commit()
            except Exception:
                pass

    def save_ic_batch(self, records: List[dict]):
        """批量保存IC记录"""
        if self._conn and records:
            try:
                self._conn.executemany("""
                    INSERT OR REPLACE INTO ic_history
                    (date, factor_name, ic, p_value, n_stocks)
                    VALUES (:date, :factor, :ic, :p_value, :n_stocks)
                """, records)
                self._conn.commit()
            except Exception:
                pass

    def get_ic_history(self, factor_name: Optional[str] = None,
                       window: int = 60) -> List[dict]:
        """获取IC历史

        Args:
            factor_name: 因子名（不传则返回所有）
            window: 最近N天

        Returns:
            [{'date','factor_name','ic','p_value','n_stocks'}, ...]
        """
        if not self._conn:
            return []
        try:
            if factor_name:
                cursor = self._conn.execute("""
                    SELECT date, factor_name, ic, p_value, n_stocks
                    FROM ic_history
                    WHERE factor_name = ?
                    ORDER BY date DESC LIMIT ?
                """, (factor_name, window))
            else:
                cursor = self._conn.execute("""
                    SELECT date, factor_name, ic, p_value, n_stocks
                    FROM ic_history
                    ORDER BY date DESC LIMIT ?
                """, (window * 35,))  # 35个因子 x window
            rows = cursor.fetchall()
            return [
                {'date': r[0], 'factor': r[1], 'ic': r[2],
                 'p_value': r[3], 'n_stocks': r[4]}
                for r in rows
            ]
        except Exception:
            return []

    def update_factor_status(self, factor_name: str, category: str,
                              mean_ic: float, ic_ir: float,
                              positive_ratio: float, n_days: int):
        """更新因子状态"""
        if not self._conn:
            return
        # 判断状态
        if mean_ic < 0.01 or positive_ratio < 0.45:
            status = 'eliminated'
        elif mean_ic < 0.02 or positive_ratio < 0.50:
            status = 'watch'
        else:
            status = 'active'

        try:
            self._conn.execute("""
                INSERT OR REPLACE INTO factor_status
                (factor_name, category, mean_ic, ic_ir, positive_ratio,
                 n_days, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (factor_name, category, mean_ic, ic_ir,
                   positive_ratio, n_days, status))
            self._conn.commit()
        except Exception:
            pass

    def get_factor_status(self, status: Optional[str] = None) -> List[dict]:
        """获取因子状态列表

        Args:
            status: 过滤状态 (active/watch/eliminated)

        Returns:
            [{'factor_name','category','mean_ic','ic_ir',
              'positive_ratio','n_days','status'}, ...]
        """
        if not self._conn:
            return []
        try:
            if status:
                cursor = self._conn.execute(
                    "SELECT * FROM factor_status WHERE status = ? "
                    "ORDER BY mean_ic DESC", (status,))
            else:
                cursor = self._conn.execute(
                    "SELECT * FROM factor_status ORDER BY mean_ic DESC")
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, r)) for r in cursor.fetchall()]
        except Exception:
            return []

    def clear(self):
        """清空缓存"""
        self._cache.clear()

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _get_db_path(self) -> str:
        if self._config:
            path = self._config.get('data.db_path', '')
            if path:
                dirname = os.path.dirname(path)
                return os.path.join(dirname, 'factors.db')
        # 默认指向 workspace 根目录下的 data/factors.db
        # __file__ 在 alice_quant/features/store.py
        # 往上3层到 workspace 根目录
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                           'data', 'factors.db')