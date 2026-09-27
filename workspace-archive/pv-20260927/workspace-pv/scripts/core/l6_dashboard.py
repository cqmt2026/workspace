# -*- coding: utf-8 -*-
"""
光伏获客系统 - L6战略层：ROI Dashboard
基于attribution数据生成策略报告，输出到data/output/
"""
import sys, os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import PVDatabase


class ROIDashboard:
    """ROI战略看板 — 分析各渠道/模板/方向的转化效率"""

    def __init__(self):
        self.db = PVDatabase()
        self.output_dir = BASE / "data" / "output" / "dashboard"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_summary(self) -> Dict:
        """获取整体概览数据"""
        cur = self.db.conn.cursor()

        # 内容总数
        cur.execute("SELECT count(*) FROM content_items")
        total = cur.fetchone()[0]

        # 已发布数
        cur.execute("SELECT count(*) FROM content_items WHERE status=?", ("published",))
        published = cur.fetchone()[0]

        # 草稿数
        cur.execute("SELECT count(*) FROM content_items WHERE status=?", ("draft",))
        draft = cur.fetchone()[0]

        # 线索数
        cur.execute("SELECT count(*) FROM leads")
        leads = cur.fetchone()[0]

        # 归因记录数
        cur.execute("SELECT count(*) FROM attribution")
        attributions = cur.fetchone()[0]

        # 成交金额
        cur.execute("SELECT COALESCE(SUM(close_amount), 0) FROM attribution WHERE converted=1")
        total_revenue = cur.fetchone()[0]

        # 渠道分布
        cur.execute("""
            SELECT channel, count(*) as cnt 
            FROM content_items 
            GROUP BY channel 
            ORDER BY cnt DESC
        """)
        channel_dist = {r[0]: r[1] for r in cur.fetchall()}

        # 方向分布（用channel代替）
        cur.execute("""
            SELECT channel, count(*) as cnt 
            FROM content_items 
            GROUP BY channel 
            ORDER BY cnt DESC
        """)
        direction_dist = {r[0]: r[1] for r in cur.fetchall()}

        return {
            "total": total,
            "published": published,
            "draft": draft,
            "leads": leads,
            "attributions": attributions,
            "total_revenue": total_revenue,
            "channel_distribution": channel_dist,
            "direction_distribution": direction_dist,
        }

    def get_channel_roi(self) -> List[Dict]:
        """各渠道ROI分析"""
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT 
                ci.channel,
                count(DISTINCT ci.content_id) as contents,
                count(DISTINCT a.id) as attributions,
                count(DISTINCT a.lead_id) as leads,
                COALESCE(SUM(CASE WHEN a.converted=1 THEN a.close_amount ELSE 0 END), 0) as revenue
            FROM content_items ci
            LEFT JOIN attribution a ON ci.content_id = a.content_id
            GROUP BY ci.channel
            ORDER BY revenue DESC
        """)
        results = []
        for r in cur.fetchall():
            results.append({
                "channel": r[0],
                "contents": r[1],
                "attributions": r[2],
                "leads": r[3],
                "revenue": r[4],
                "avg_revenue_per_content": round(r[4] / r[1], 2) if r[1] > 0 else 0,
            })
        return results

    def get_template_performance(self) -> List[Dict]:
        """各渠道表现（用channel代替template_used）"""
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT 
                ci.channel as direction,
                count(*) as contents,
                count(DISTINCT a.id) as attributions,
                COALESCE(SUM(CASE WHEN a.converted=1 THEN a.close_amount ELSE 0 END), 0) as revenue
            FROM content_items ci
            LEFT JOIN attribution a ON ci.content_id = a.content_id
            GROUP BY ci.channel
            ORDER BY revenue DESC
        """)
        results = []
        for r in cur.fetchall():
            results.append({
                "direction": r[0],
                "contents": r[1],
                "attributions": r[2],
                "revenue": r[3],
                "conversion_rate": round(r[2] / r[1] * 100, 1) if r[1] > 0 else 0,
            })
        return results

    def generate_report(self) -> str:
        """生成完整报告"""
        summary = self.get_summary()
        channel_roi = self.get_channel_roi()
        template_perf = self.get_template_performance()

        lines = []
        lines.append("=" * 60)
        lines.append("  光伏获客系统 — ROI战略看板")
        lines.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 60)

        # 一、整体概览
        lines.append("\n【一、整体概览】")
        lines.append(f"  总内容数:     {summary['total']}")
        lines.append(f"  已发布:       {summary['published']}")
        lines.append(f"  草稿中:       {summary['draft']}")
        lines.append(f"  线索池:       {summary['leads']} 条")
        lines.append(f"  归因记录:     {summary['attributions']} 条")
        lines.append(f"  成交金额:     ¥{summary['total_revenue']:,.2f}")

        if summary["total"] > 0:
            publish_rate = summary["published"] / summary["total"] * 100
            lines.append(f"  发布率:       {publish_rate:.1f}%")
        if summary["attributions"] > 0:
            conv_rate = summary["attributions"] / summary["published"] * 100 if summary["published"] > 0 else 0
            lines.append(f"  归因率:       {conv_rate:.1f}%")

        # 二、渠道ROI
        lines.append("\n【二、渠道ROI分析】")
        if channel_roi:
            for ch in channel_roi:
                lines.append(f"  {ch['channel']:<10} 内容:{ch['contents']:>3}  归因:{ch['attributions']:>3}  收入:¥{ch['revenue']:>10,.2f}  单条均收:¥{ch['avg_revenue_per_content']:>8,.2f}")
        else:
            lines.append("  （暂无数据，需要先回填内容效果数据）")

        # 三、模板表现
        lines.append("\n【三、模板方向表现】")
        if template_perf:
            for tp in template_perf:
                lines.append(f"  {tp['direction']:<12} 内容:{tp['contents']:>3}  归因:{tp['attributions']:>3}  收入:¥{tp['revenue']:>10,.2f}  转化率:{tp['conversion_rate']:>5.1f}%")
        else:
            lines.append("  （暂无数据）")

        # 四、策略建议
        lines.append("\n【四、策略建议】")
        if not channel_roi or not template_perf:
            lines.append("  ⚠️ 当前缺少效果数据回填，无法生成策略建议。")
            lines.append("  建议：")
            lines.append("  1. 每天手动回填已发布内容的播放/互动/线索数据")
            lines.append("  2. 在douyin.py/toutiao.py的get_performance()中对接API自动拉取")
            lines.append("  3. 积累1周数据后可自动生成优化建议")
        else:
            # 自动建议
            best_channel = channel_roi[0] if channel_roi else None
            best_template = template_perf[0] if template_perf else None
            if best_channel:
                lines.append(f"  ✅ 最佳渠道: {best_channel['channel']} (收入¥{best_channel['revenue']:,.2f})")
            if best_template:
                lines.append(f"  ✅ 最佳方向: {best_template['direction']} (转化率{best_template['conversion_rate']}%)")
            lines.append("  💡 建议加大高效渠道/方向的投放比例")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def save_report(self) -> Path:
        """保存报告到文件"""
        report_text = self.generate_report()
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = self.output_dir / f"l6_dashboard_{date_str}.txt"
        filepath.write_text(report_text, encoding="utf-8")
        return filepath

    def close(self):
        self.db.close()


if __name__ == "__main__":
    dashboard = ROIDashboard()
    filepath = dashboard.save_report()
    print(f"[Saved] {filepath}")
    dashboard.close()
