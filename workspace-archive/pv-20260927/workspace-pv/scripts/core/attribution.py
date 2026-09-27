# -*- coding: utf-8 -*-
"""
光伏获客系统 - 归因分析模块 v0.1
L5反馈层核心：追踪内容发布效果，回灌到模板权重调整

职责：
1. 内容发布后回填效果数据（播放/互动/线索）
2. 归因分析：记录线索来源→成交→渠道/模板ROI
3. 模板权重反馈：根据归因结果调整模板使用频率
"""
import sys, os, json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import PVDatabase
from core.industry_plugin_loader import get_plugin


class AttributionEngine:
    """归因引擎"""

    def __init__(self, industry: str = "solar"):
        self.db = PVDatabase()
        self.plugin = get_plugin(industry)

    # ========== 发布后回填 ==========

    def record_publish(self, tracking_id: str, channel: str, url: str = "",
                       status: str = "published") -> bool:
        """记录内容发布（tracking_id作为content_id存储）"""
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            cur = self.db.conn.cursor()
            cur.execute("""
                UPDATE content_items
                SET status=?, published_at=?, tracking_id=?
                WHERE content_id=?
            """, (status, now, tracking_id, tracking_id))
            if cur.rowcount == 0:
                cur.execute("""
                    INSERT INTO content_items
                    (content_id, tracking_id, channel, status, published_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (tracking_id, tracking_id, channel, status, now))
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.log_action("attribution", "record_publish", "error", str(e)[:200])
            return False

    def update_performance(self, content_id: str, plays: int = 0,
                           likes: int = 0, comments: int = 0,
                           shares: int = 0, leads_generated: int = 0) -> bool:
        """回填效果数据"""
        try:
            cur = self.db.conn.cursor()
            cur.execute("""
                UPDATE content_items
                SET plays=plays+?, leads_generated=leads_generated+?
                WHERE content_id=?
            """, (plays, leads_generated, content_id))
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.log_action("attribution", "update_performance", "error", str(e)[:200])
            return False

    # ========== 线索归因 ==========

    def record_lead(self, content_id: str, channel: str, name: str = "",
                    phone: str = "", level: str = "C", tags: str = "") -> int:
        """记录线索来源"""
        try:
            # 写入leads
            cur = self.db.conn.cursor()
            cur.execute("""
                INSERT INTO leads
                (source_channel, source_content_id, name, phone, level, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (channel, content_id, name, phone, level, tags))
            lead_id = cur.lastrowid

            # 写入attribution
            cur.execute("""
                INSERT INTO attribution
                (content_id, channel, lead_id, converted)
                VALUES (?, ?, ?, 0)
            """, (content_id, channel, lead_id))

            self.db.conn.commit()
            return lead_id
        except Exception as e:
            self.db.log_action("attribution", "record_lead", "error", str(e)[:200])
            return 0

    def mark_converted(self, lead_id: int, close_amount: float = 0) -> bool:
        """标记线索成交"""
        try:
            cur = self.db.conn.cursor()
            cur.execute("""
                UPDATE attribution
                SET converted=1, close_amount=?
                WHERE lead_id=?
            """, (close_amount, lead_id))
            # 同步更新leads等级
            cur.execute("""
                UPDATE leads SET level='A' WHERE id=?
            """, (lead_id,))
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.log_action("attribution", "mark_converted", "error", str(e)[:200])
            return False

    # ========== 归因分析 ==========

    def get_content_roi(self, content_id: str) -> Dict:
        """单条内容ROI分析"""
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT ci.*, COUNT(a.id) as leads_count,
                   SUM(CASE WHEN a.converted=1 THEN 1 ELSE 0 END) as conversions,
                   SUM(a.close_amount) as total_close_amount
            FROM content_items ci
            LEFT JOIN attribution a ON ci.content_id = a.content_id
            WHERE ci.content_id = ?
            GROUP BY ci.id
        """, (content_id,))
        row = cur.fetchone()
        if not row:
            return {"status": "not_found"}
        r = dict(row)
        r["conversion_rate"] = round(r["conversions"] / max(r["leads_count"], 1), 2)
        return r

    def get_channel_roi(self, channel: str, days: int = 30) -> Dict:
        """渠道ROI分析"""
        cur = self.db.conn.cursor()
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cur.execute("""
            SELECT COUNT(*) as content_count,
                   SUM(plays) as total_plays,
                   SUM(leads_generated) as total_leads,
                   SUM(CASE WHEN a.converted=1 THEN 1 ELSE 0 END) as conversions,
                   SUM(a.close_amount) as total_close_amount
            FROM content_items ci
            LEFT JOIN attribution a ON ci.content_id = a.content_id
            WHERE ci.channel = ? AND ci.created_at >= ?
        """, (channel, since))
        row = cur.fetchone()
        if not row:
            return {"status": "no_data", "channel": channel}
        r = dict(row)
        r["channel"] = channel
        r["days"] = days
        r["lead_to_conv_rate"] = round(r["conversions"] / max(r["total_leads"], 1), 2)
        return r

    def get_template_performance(self, days: int = 7) -> List[Dict]:
        """模板方向表现对比"""
        cur = self.db.conn.cursor()
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cur.execute("""
            SELECT cg.direction, ci.channel,
                   COUNT(*) as content_count,
                   AVG(ci.plays) as avg_plays,
                   AVG(ci.leads_generated) as avg_leads
            FROM content_items ci
            LEFT JOIN (
                SELECT content_id, direction FROM content_generated
            ) cg ON ci.content_id = cg.content_id
            WHERE ci.created_at >= ?
            GROUP BY cg.direction, ci.channel
            ORDER BY avg_plays DESC
        """, (since,))
        return [dict(r) for r in cur.fetchall()]

    # ========== 权重反馈 ==========

    def adjust_template_weights(self, days: int = 30) -> Dict:
        """根据归因数据调整模板权重"""
        # 获取各方向表现
        perf = self.get_template_performance(days)
        if not perf:
            return {"status": "no_data"}

        # 按平均播放量计算权重
        total_plays = sum(p.get("avg_plays", 0) or 0 for p in perf)
        if total_plays == 0:
            return {"status": "no_plays"}

        weights = {}
        for p in perf:
            direction = p.get("direction", "unknown")
            avg_plays = p.get("avg_plays", 0) or 0
            weight = round(avg_plays / total_plays, 2)
            weights[direction] = {
                "weight": weight,
                "avg_plays": avg_plays,
                "avg_leads": p.get("avg_leads", 0) or 0,
            }

        # 更新到插件配置（暂存到文件，后续可持久化）
        plugin = self.plugin
        weights_path = plugin.plugin_dir / "template_weights.json"
        with open(weights_path, "w", encoding="utf-8") as f:
            json.dump(weights, f, ensure_ascii=False, indent=2)

        return {"status": "updated", "weights": weights, "based_on_days": days}

    def get_content_summary(self, days: int = 7) -> Dict:
        """内容效果总览"""
        cur = self.db.conn.cursor()
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cur.execute("""
            SELECT channel, status, COUNT(*) as cnt,
                   SUM(plays) as total_plays,
                   SUM(leads_generated) as total_leads
            FROM content_items
            WHERE created_at >= ?
            GROUP BY channel, status
        """, (since,))
        rows = [dict(r) for r in cur.fetchall()]

        cur.execute("""
            SELECT COUNT(*) as total_leads,
                   SUM(CASE WHEN converted=1 THEN 1 ELSE 0 END) as conversions,
                   SUM(close_amount) as total_revenue
            FROM attribution
            WHERE created_at >= ?
        """, (since,))
        attr_summary = dict(cur.fetchone())

        return {
            "days": days,
            "content_by_channel": rows,
            "attribution_summary": attr_summary,
        }

    def close(self):
        self.db.close()


if __name__ == "__main__":
    engine = AttributionEngine()
    print("=== S3 Attribution Engine ===")
    print(f"Plugin: {engine.plugin.industry}")

    # 测试：记录发布
    test_id = f"PV_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    engine.record_publish(test_id, "douyin", "https://example.com")
    print(f"  Record publish: {test_id}")

    # 测试：回填效果
    engine.update_performance(test_id, plays=1000, likes=50, leads_generated=3)
    print(f"  Update performance: plays=1000")

    # 测试：记录线索
    lid = engine.record_lead(test_id, "douyin", "测试客户", "13600136000", "B", "报价")
    print(f"  Record lead: id={lid}")

    # 测试：归因分析
    roi = engine.get_content_roi(test_id)
    print(f"  Content ROI: {roi}")

    # 测试：汇总
    summary = engine.get_content_summary(30)
    print(f"  Summary: {summary['attribution_summary']}")

    engine.close()
    print("  [OK] Attribution Engine test complete")