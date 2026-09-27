# -*- coding: utf-8 -*-
"""
光伏获客系统 - 竞品内容分析模块 v0.1
分析竞品账号的内容策略：发布频率、内容方向、爆款特征

注：当前版本为占位实现，实际竞品内容需通过抖音/头条API或Playwright采集。
此处先做框架设计+手动录入接口。
"""
import sys, os, json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

if sys.platform == 'win32':
    pass  # encoding handled by integration_test

from core.database import PVDatabase


class CompetitorContentAnalyzer:
    """竞品内容分析器"""

    # 预设爆款特征规则（后续可从数据中学习）
    VIRAL_RULES = {
        "title_length_short": (0, 15, 1.2),       # 标题15字以内权重×1.2
        "title_length_medium": (15, 30, 1.5),     # 15-30字权重×1.5
        "title_has_number": (None, None, 1.3),    # 含数字标题权重×1.3
        "title_has_question": (None, None, 1.1),  # 含问号标题权重×1.1
        "direction_policy": ("policy", None, 1.4), # 政策解读权重×1.4
        "direction_benefit": ("benefit", None, 1.3),# 收益计算权重×1.3
        "direction_avoid": ("avoid", None, 1.5),   # 避坑指南权重×1.5
    }

    def __init__(self):
        self.db = PVDatabase()

    def analyze_competitor(self, platform: str, account_name: str) -> Dict:
        """分析单个竞品的内容策略"""
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT c.account_name, c.followers,
                   COUNT(cc.id) as content_count,
                   AVG(cc.play_count) as avg_plays,
                   AVG(cc.like_count) as avg_likes
            FROM competitors c
            LEFT JOIN competitor_contents cc ON c.id = cc.competitor_id
            WHERE c.platform = ? AND c.account_name = ?
            GROUP BY c.id
        """, (platform, account_name))
        row = cur.fetchone()
        if not row:
            return {"status": "not_found", "account": account_name}

        result = dict(row)
        # 分析内容方向分布
        cur.execute("""
            SELECT title, play_count, like_count, comment_count, published_at
            FROM competitor_contents
            WHERE competitor_id = ?
            ORDER BY published_at DESC LIMIT 20
        """, (result["id"],))
        contents = [dict(r) for r in cur.fetchall()]
        result["recent_contents"] = contents
        result["total_content"] = len(contents)

        return result

    def get_content_direction_hint(self, direction: str) -> Dict:
        """根据方向返回内容建议"""
        hints = {
            "policy": {
                "hook_style": "政策红利型",
                "hook_example": "重磅！{title}来了，装光伏的前先看清楚",
                "body_focus": "解读政策原文 → 对业主的实际影响 → 操作指南",
                "cta": "想知道你家能不能装？评论区留言省份+屋顶面积",
            },
            "benefit": {
                "hook_style": "算账利益型",
                "hook_example": "装5kW光伏一年赚{X}元？真实案例给你算明白",
                "body_focus": "投入成本 → 发电收益 → 回本周期 → 风险提示",
                "cta": "免费测算你家屋顶收益，私信我地址+用电情况",
            },
            "avoid": {
                "hook_style": "恐惧规避型",
                "hook_example": "90%的人装光伏都踩了这3个坑，第2个最致命",
                "body_focus": "场景代入 → 具体坑点 → 解决方案 → 信任建立",
                "cta": "装光伏前先看这条视频，评论区帮你避坑",
            },
            "news": {
                "hook_style": "行业观察型",
                "hook_example": "今天光伏圈都在讨论：{title}",
                "body_focus": "事件描述 → 行业影响 → 对普通人的意义",
                "cta": "关注我，每天解读一个光伏行业大事",
            },
            "tech": {
                "hook_style": "知识科普型",
                "hook_example": "{title}到底是什么意思？一文讲透",
                "body_focus": "概念解释 → 实际影响 → 如何判断",
                "cta": "想看更多光伏干货？关注不迷路",
            },
        }
        return hints.get(direction, hints["policy"])

    def generate_competitive_insights(self, pv_topics: List[Dict] = None) -> str:
        """基于当前热点生成竞品内容策略建议"""
        lines = []
        lines.append("=" * 55)
        lines.append("  Competitive Content Insights")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 55)

        if pv_topics is None:
            pv_topics = self.db.get_latest_pv_topics(5)

        if pv_topics:
            lines.append("\n📊 当前热点趋势:")
            for t in pv_topics[:3]:
                lines.append(f"  • {t['title'][:45]}")

            # 内容方向建议
            lines.append("\n💡 内容方向建议:")
            for t in pv_topics[:5]:
                direction = self._classify(t["title"])
                hint = self.get_content_direction_hint(direction)
                lines.append(f"\n  [{hint['hook_style']}]")
                lines.append(f"  素材: {t['title'][:40]}")
                lines.append(f"  钩子: {hint['hook_example'].format(title=t['title'][:20], X='3000')}")
                lines.append(f"  正文: {hint['body_focus']}")
                lines.append(f"  CTA: {hint['cta']}")

        lines.append("\n" + "=" * 55)
        return "\n".join(lines)

    def _classify(self, title: str) -> str:
        t = title.lower()
        if any(kw in t for kw in ["补贴", "政策", "通知", "管理办法", "意见", "标准", "规划", "细则"]):
            return "policy"
        if any(kw in t for kw in ["收益", "赚钱", "划算", "成本", "电价", "电费", "度电"]):
            return "benefit"
        if any(kw in t for kw in ["注意", "警惕", "坑", "风险", "违规", "投诉", "暂停", "预警"]):
            return "avoid"
        if any(kw in t for kw in ["装机", "GW", "并网", "中标", "采购", "投产", "业绩", "财报", "趋势"]):
            return "news"
        return "tech"

    def run(self, verbose: bool = True) -> Dict:
        contents = self.generate_competitive_insights()
        if verbose:
            print(contents)

        # 保存
        output_dir = BASE / "data" / "output"
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / f"insights_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(contents)

        self.db.close()
        return {"status": "ok", "filepath": str(filepath)}


if __name__ == "__main__":
    analyzer = CompetitorContentAnalyzer()
    analyzer.run()
