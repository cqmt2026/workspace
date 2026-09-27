# -*- coding: utf-8 -*-
"""
光伏获客系统 - 线索管理模块 v0.1
线索录入、打分分级、客户管理

职责：
1. 手动录入线索（name/phone/source/level/tags）
2. 线索打分（基于行业配置权重）
3. 线索分级（A/B/C）
4. 基础CRM（跟进记录、标签体系）
"""
import sys, os, json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import PVDatabase
from core.industry_plugin_loader import get_plugin


class LeadManager:
    """线索管理"""

    def __init__(self):
        self.db = PVDatabase()
        self.plugin = get_plugin('solar')
        self.scoring_weights = self.plugin.scoring_weights

    def add_lead(self, source_channel: str, source_content_id: str = "",
                 name: str = "", phone: str = "", level: str = "C",
                 tags: str = "") -> int:
        """录入线索"""
        cur = self.db.conn.cursor()
        cur.execute("""
            INSERT INTO leads (source_channel, source_content_id, name, phone, level, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (source_channel, source_content_id, name, phone, level, tags))
        self.db.conn.commit()
        return cur.lastrowid

    def score_lead(self, lead_id: int) -> Dict:
        """线索打分（基于tags/来源等特征）"""
        cur = self.db.conn.cursor()
        cur.execute("SELECT * FROM leads WHERE id=?", (lead_id,))
        lead = cur.fetchone()
        if not lead:
            return {"status": "not_found", "lead_id": lead_id}

        tags = lead["tags"] or ""
        source = lead["source_channel"] or ""

        score = 0
        reasons = []

        # 来源权重
        if source == "douyin":
            score += self.scoring_weights.get("ask_price", 0)
            reasons.append("抖音来源(+30)")
        elif source == "toutiao":
            score += self.scoring_weights.get("ask_process", 0)
            reasons.append("头条来源(+20)")

        # 标签权重
        if "报价" in tags or "价格" in tags:
            score += 20
            reasons.append("询价意图(+20)")
        if "安装" in tags or "并网" in tags:
            score += 15
            reasons.append("安装意向(+15)")
        if "政策" in tags:
            score += 10
            reasons.append("政策关注(+10)")

        # 等级判定
        if score >= 50:
            level = "A"
        elif score >= 30:
            level = "B"
        else:
            level = "C"

        # 更新等级
        cur.execute("UPDATE leads SET level=? WHERE id=?", (level, lead_id))
        self.db.conn.commit()

        return {
            "lead_id": lead_id,
            "score": score,
            "level": level,
            "reasons": reasons,
        }

    def get_leads(self, level: str = None, limit: int = 20,
                  offset: int = 0) -> List[Dict]:
        """查询线索列表"""
        cur = self.db.conn.cursor()
        if level:
            cur.execute(
                "SELECT * FROM leads WHERE level=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (level, limit, offset)
            )
        else:
            cur.execute(
                "SELECT * FROM leads ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
        return [dict(r) for r in cur.fetchall()]

    def add_followup(self, lead_id: int, note: str, action: str = "") -> int:
        """添加跟进记录（存到system_logs方便查询）"""
        self.db.log_action("crm", "followup", "ok",
            f"lead_id={lead_id}, action={action}, note={note[:200]}")
        return lead_id

    def get_stats(self) -> Dict:
        """线索统计"""
        cur = self.db.conn.cursor()
        stats = {}
        for lvl in ['A', 'B', 'C']:
            cur.execute("SELECT COUNT(*) FROM leads WHERE level=?", (lvl,))
            stats[f"{lvl}_count"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM leads")
        stats["total"] = cur.fetchone()[0]
        return stats


if __name__ == "__main__":
    lm = LeadManager()
    # 测试录入
    lid = lm.add_lead("douyin", "PV_20260818_171134", "测试客户", "13800138000", "C", "报价")
    print(f"Lead added: id={lid}")
    result = lm.score_lead(lid)
    print(f"Scored: {result}")
    print(f"Stats: {lm.get_stats()}")
