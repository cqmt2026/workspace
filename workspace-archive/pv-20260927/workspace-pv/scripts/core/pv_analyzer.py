# -*- coding: utf-8 -*-
"""
光伏获客系统 - 数据分析层
v0.1
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))
os.chdir(str(BASE))

from core.database import PVDatabase


class PVAnalyzer:
    """光伏数据分析器"""

    def __init__(self):
        self.db = PVDatabase()

    def analyze_hot_trends(self, days: int = 7) -> Dict:
        cur = self.db.conn.cursor()

        cur.execute("""
            SELECT date(collected_at) as d, COUNT(*) as cnt
            FROM hot_topics
            WHERE pv_related = 1
              AND collected_at >= datetime('now', 'localtime', ?)
            GROUP BY d ORDER BY d
        """, (f"-{days} days",))
        daily_counts = [dict(row) for row in cur.fetchall()]

        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT keywords, COUNT(*) as cnt
            FROM hot_topics
            WHERE pv_related = 1 AND keywords != ''
              AND collected_at >= datetime('now', 'localtime', ?)
            GROUP BY keywords ORDER BY cnt DESC LIMIT 20
        """, (f"-{days} days",))
        keywords = [dict(row) for row in cur.fetchall()]

        cur.execute("""
            SELECT source, COUNT(*) as cnt
            FROM hot_topics
            WHERE pv_related = 1 AND collected_at >= datetime('now', 'localtime', ?)
            GROUP BY source
        """, (f"-{days} days",))
        source_dist = [dict(row) for row in cur.fetchall()]

        cur.execute("""
            SELECT AVG(hot_score) as avg_score, MAX(hot_score) as max_score
            FROM hot_topics
            WHERE pv_related = 1
              AND collected_at >= datetime('now', 'localtime', ?)
        """, (f"-{days} days",))
        score_stats = dict(cur.fetchone()) or {"avg_score": 0, "max_score": 0}

        return {
            "daily_counts": daily_counts,
            "top_keywords": keywords,
            "source_distribution": source_dist,
            "score_stats": score_stats,
            "total_pv_topics": sum(r["cnt"] for r in daily_counts),
        }

    def get_hot_topics_for_content(self, limit: int = 10) -> List[Dict]:
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT title, source, hot_score, pv_score, collected_at
            FROM hot_topics
            WHERE pv_related = 1 AND hot_score > 0
            ORDER BY hot_score * pv_score DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]

    def generate_summary_report(self) -> str:
        trends = self.analyze_hot_trends()
        hot_topics = self.get_hot_topics_for_content(5)

        lines = ["📈 光伏热点分析报告", "=" * 40]
        lines.append(f"分析周期: 近7天")
        lines.append(f"光伏相关话题: {trends['total_pv_topics']} 条")

        avg_score = trends['score_stats']['avg_score']
        lines.append(f"平均热度: {avg_score:.0f}" if avg_score else "平均热度: N/A")
        lines.append("")

        if trends["source_distribution"]:
            lines.append("📡 来源分布:")
            for s in trends["source_distribution"]:
                lines.append(f"  {s['source']}: {s['cnt']} 条")

        if hot_topics:
            lines.append("\n🔥 当前热点:")
            for t in hot_topics:
                lines.append(f"  {t['title']} (热度:{t['hot_score']})")

        return "\n".join(lines)