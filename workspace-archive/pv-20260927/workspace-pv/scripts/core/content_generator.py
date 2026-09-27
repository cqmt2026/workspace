# -*- coding: utf-8 -*-
"""
光伏获客系统 - 内容生成模块 v0.4
从热点+政策中提取素材，自动生成获客内容脚本（短视频/图文）
S3: 追踪ID注入 + attribution自动记录
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

if sys.platform == 'win32':
    try:
        import io
        if sys.stdout and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except (ValueError, OSError):
        pass  # stdout已关闭，忽略

from core.database import PVDatabase
from core.industry_plugin_loader import get_plugin
from core.template_engine import TemplateEngine
from core.llm_enhancer import SolarLLMClient, enhance_content
from core.tracker import Tracker
from core.attribution import AttributionEngine
from core.geo_region import GeoRegionData, HIGH_POTENTIAL_PROVINCES
from core.channel.base import ContentPack
from core.channel.douyin import DouyinChannel
from core.channel.toutiao import ToutiaoChannel
from core.channel.wechat import WechatChannel
from core.l6_dashboard import ROIDashboard


class ContentGenerator:
    """光伏获客内容生成器 — v0.4 S3追踪ID+归因"""

    DIRECTION_NAMES = {
        "policy": "政策解读",
        "benefit": "收益计算",
        "avoid": "避坑指南",
        "news": "行业新闻",
        "tech": "技术科普",
    }

    DIRECTION_TARGETS = {
        "policy": "想装光伏、关心补贴和流程的业主",
        "benefit": "在意投资回报、算账的自建房业主",
        "avoid": "怕踩坑、需要信任决策的业主",
        "news": "关注行业动态、有商业决策的老板/投资人",
        "tech": "想深入了解技术、建立专业认知的用户",
    }

    def __init__(self, use_llm: bool = False, auto_record: bool = True):
        self.db = PVDatabase()
        self.plugin = get_plugin('solar')
        self.engine = TemplateEngine('solar')
        self.use_llm = use_llm
        self.geo = GeoRegionData()  # GEO区域评分引擎
        self.llm_client = SolarLLMClient() if use_llm else None
        self.tracker = Tracker()
        self.auto_record = auto_record
        self.attribution = AttributionEngine('solar') if auto_record else None

    def _classify(self, title: str) -> str:
        return self.plugin.classify_direction(title)

    def _build_script(self, topic: Dict, direction: str, policy: Dict = None) -> Dict:
        engine_result = self.engine.render_template(direction, topic, policy)
        tracking_id = self.tracker.generate_id(channel="pv")

        result = {
            "direction": direction,
            "direction_name": self.DIRECTION_NAMES.get(direction, direction),
            "source_title": topic.get("title", ""),
            "source_url": topic.get("url", ""),
            "source": topic.get("source", ""),
            "hook": engine_result.get("hook", ""),
            "body": engine_result.get("body", ""),
            "cta": engine_result.get("cta", ""),
            "full_script": engine_result.get("full_script", ""),
            "target_audience": self.DIRECTION_TARGETS.get(direction, ""),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "template_used": engine_result.get("template_used", "fallback"),
            "tracking_id": tracking_id,
            "enhanced": False,
        }

        # LLM增强
        if self.use_llm and self.llm_client and self.llm_client.is_available():
            result = enhance_content(result, self.llm_client)

        # S3: 自动记录到content_items
        if self.auto_record and self.attribution:
            self.attribution.record_publish(tracking_id, "douyin")

        return result

    def _select_target_provinces(self, topic: Dict) -> List[str]:
        """根据热点标题中的省份信息，选择目标投放省份"""
        title = topic.get("title", "")
        provinces_in_title = []
        # 从plugin加载的省份列表
        for p in self.plugin.provinces:
            if p in title:
                provinces_in_title.append(p)
        if provinces_in_title:
            return provinces_in_title
        # 默认按GEO评分排序，取Top3
        sorted_provs = sorted(
            HIGH_POTENTIAL_PROVINCES,
            key=lambda x: x["score"], reverse=True
        )
        return [p["province"] for p in sorted_provs[:3]]

    def generate_daily_content(self, limit_topics: int = 6, limit_policies: int = 4) -> List[Dict]:
        topics = self.db.get_latest_pv_topics(limit_topics)
        policies = self.db.get_latest_policies(limit_policies)

        contents = []
        for t in topics:
            direction = self._classify(t["title"])
            policy = None
            if direction == "policy" and policies:
                policy = policies[0]
            content = self._build_script(t, direction, policy)
            # GEO: 为内容添加目标省份和评分
            target_provinces = self._select_target_provinces(t)
            content["target_provinces"] = target_provinces
            content["geo_primary_province"] = target_provinces[0] if target_provinces else "全国"
            content["geo_score"] = self.geo.get_province_score(target_provinces[0]) if target_provinces else 0
            contents.append(content)
        return contents

    def generate_report(self, contents: List[Dict]) -> str:
        lines = []
        lines.append("=" * 55)
        lines.append("  Solar PV Content Suggestions (v0.4-S3)")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 55)

        for i, c in enumerate(contents, 1):
            enhanced_tag = " [LLM]" if c.get("enhanced") else ""
            tid_tag = f" ID:{c.get('tracking_id','?')[-8:]}"
            lines.append(f"\n[{i}] {c['direction_name']}{enhanced_tag}{tid_tag}")
            lines.append(f"  素材: {c['source_title'][:45]}")
            lines.append(f"  目标: {c['target_audience']}")
            lines.append("  ---")
            lines.append(f"  钩子: {c['hook']}")
            lines.append(f"  正文: {c['body'][:120]}...")
            lines.append(f"  CTA: {c['cta'][:80]}")

        lines.append("\n" + "=" * 55)
        lines.append(f"总计: {len(contents)}条 | 追踪ID已注入")
        return "\n".join(lines)

    def save_report(self, report_text: str, filename: str = None) -> Path:
        output_dir = BASE / "data" / "output"
        output_dir.mkdir(exist_ok=True)
        if filename is None:
            filename = f"content_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        filepath = output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_text)
        return filepath

    def save_single_scripts(self, contents: List[Dict]) -> Path:
        output_dir = BASE / "data" / "content"
        output_dir.mkdir(exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        for i, c in enumerate(contents, 1):
            seq = f"{date_str}_{i:02d}"
            filepath = output_dir / f"{seq}_{c['direction_name']}.txt"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"【{c['direction_name']}】{c['source_title']}\n")
                f.write(f"目标人群: {c['target_audience']}\n")
                f.write(f"来源: {c['source']} | 生成时间: {c['generated_at']}\n")
                f.write(f"追踪ID: {c.get('tracking_id', 'N/A')}\n")
                if c.get("enhanced"):
                    f.write("生成方式: LLM增强\n")
                f.write("=" * 40 + "\n\n")
                f.write(c["full_script"])
                f.write("\n\n" + "=" * 40 + "\n")
                f.write(f"参考链接: {c['source_url']}\n")
        return output_dir

    def _export_channels(self, contents: List[Dict]) -> Dict:
        """将内容分发到各渠道，返回导出结果"""
        results = {"douyin": [], "toutiao": [], "wechat": []}
        channels = [DouyinChannel(), ToutiaoChannel(), WechatChannel()]
        for ch in channels:
            for c in contents:
                pack = ContentPack(
                    title=c.get("source_title", ""),
                    hook=c["hook"],
                    body=c["body"],
                    cta=c["cta"],
                    channel=ch.CHANNEL_NAME,
                    industry="solar",
                    template_used=c.get("template_used", "fallback"),
                    tracking_id=c.get("tracking_id", ""),
                )
                pub = ch.publish(pack)
                results[ch.CHANNEL_NAME].append({
                    "tracking_id": c.get("tracking_id"),
                    "success": pub.success,
                    "url": str(pub.url) if pub.url else None,
                    "error": pub.error,
                })
        return results

    def run(self, verbose: bool = True) -> Dict:
        contents = self.generate_daily_content()
        report = self.generate_report(contents)
        report_path = self.save_report(report)
        scripts_dir = self.save_single_scripts(contents)
        channel_results = self._export_channels(contents)

        # 安全输出：避免Windows Cron环境下stdout closed报错
        try:
            if verbose:
                print(report)
                print(f"\n[Saved] Report: {report_path}")
                print(f"[Saved] Scripts: {scripts_dir}/")
                dy_ok = sum(1 for r in channel_results["douyin"] if r["success"])
                tt_ok = sum(1 for r in channel_results["toutiao"] if r["success"])
                dy_ok = sum(1 for r in channel_results["douyin"] if r["success"])
                tt_ok = sum(1 for r in channel_results["toutiao"] if r["success"])
                wx_ok = sum(1 for r in channel_results["wechat"] if r["success"])
                print(f"[Channels] Douyin: {dy_ok}/{len(contents)}, Toutiao: {tt_ok}/{len(contents)}, Wechat: {wx_ok}/{len(contents)}")
        except (ValueError, OSError):
            pass  # stdout closed，忽略输出

        self.db.close()
        if self.attribution:
            self.attribution.close()

        # L6: 生成ROI战略看板
        try:
            dashboard = ROIDashboard()
            dashboard_path = dashboard.save_report()
            dashboard.close()
            channel_results["dashboard"] = str(dashboard_path)
        except Exception:
            pass  # dashboard生成失败不影响主流程

        return {
            "count": len(contents),
            "report_path": str(report_path),
            "scripts_dir": str(scripts_dir),
            "contents": contents,
            "llm_used": self.use_llm and self.llm_client is not None,
            "tracking_ids": [c["tracking_id"] for c in contents],
            "channels": channel_results,
        }


if __name__ == "__main__":
    gen = ContentGenerator(use_llm=True, auto_record=True)
    result = gen.run()
    try:
        print(f"\n[Complete] Generated {result['count']} pieces, "
              f"IDs: {result['tracking_ids'][:2]}...")
    except (ValueError, OSError):
        pass
