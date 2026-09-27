# -*- coding: utf-8 -*-
"""微信公众号渠道适配器 - 导出格式"""
import sys, os
from pathlib import Path
from typing import List, Dict
from datetime import datetime

BASE = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))

from core.channel.base import ChannelAdapter, ContentPack, PublishResult, PerformanceData
from core.database import PVDatabase


class WechatChannel(ChannelAdapter):
    """微信公众号渠道适配器
    
    导出格式：公众号图文排版（Markdown转HTML兼容格式）
    """
    
    CHANNEL_NAME = "wechat"
    
    def __init__(self):
        self.db = PVDatabase()
    
    def publish(self, content_pack: ContentPack) -> PublishResult:
        try:
            tracking_id = content_pack.tracking_id or f"WX_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            publish_data = self._format_for_wechat(content_pack, tracking_id)
            
            output_dir = BASE / "data" / "output" / "wechat"
            output_dir.mkdir(parents=True, exist_ok=True)
            filepath = output_dir / f"{tracking_id}.md"
            filepath.write_text(publish_data, encoding="utf-8")
            
            self.db.save_content_item(tracking_id, self.CHANNEL_NAME, tracking_id=tracking_id, 
                                     filepath=str(filepath), status="published")
            
            return PublishResult(success=True, item_id=tracking_id, url=str(filepath))
        except Exception as e:
            return PublishResult(success=False, error=str(e))
    
    def _format_for_wechat(self, pack: ContentPack, tracking_id: str) -> str:
        """格式化公众号发布内容"""
        lines = []
        lines.append(f"# 公众号发布包 | {tracking_id}")
        lines.append(f"生成时间: {pack.generated_at}")
        lines.append("")
        lines.append("## 标题（≤64字，建议20-40字）")
        lines.append(pack.hook[:40] if len(pack.hook) > 40 else pack.hook)
        lines.append("")
        lines.append("## 摘要（≤120字，用于封面展示）")
        summary = pack.body[:100] + "..." if len(pack.body) > 100 else pack.body
        lines.append(summary)
        lines.append("")
        lines.append("## 正文（可直接复制到公众号编辑器）")
        lines.append(pack.body)
        lines.append("")
        lines.append("## CTA引导")
        lines.append(pack.cta)
        lines.append("")
        lines.append("## 建议")
        lines.append(f"- 追踪ID: {tracking_id}")
        lines.append(f"- 模板方向: {getattr(pack, 'template_used', 'news')}")
        lines.append(f"- 行业: {getattr(pack, 'industry', 'solar')}")
        lines.append("- 最佳发布时间: 早7-8点 / 午12-13点 / 晚20-22点")
        lines.append("- 公众号用户偏好：深度解读 > 情绪渲染 > 数据罗列")
        lines.append("")
        lines.append("---")
        lines.append(f"*本文由光伏获客系统自动生成 | tracking_id: {tracking_id}*")
        return "\n".join(lines)
    
    def get_performance(self, item_id: str) -> PerformanceData:
        return PerformanceData()
    
    def collect_leads(self) -> List[Dict]:
        return []


if __name__ == "__main__":
    print("Wechat channel adapter loaded")
