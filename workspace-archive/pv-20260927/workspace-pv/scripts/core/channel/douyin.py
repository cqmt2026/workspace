# -*- coding: utf-8 -*-
"""抖音渠道适配器 - 导出格式（无API版）"""
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# 添加父目录到path
BASE = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))

from core.channel.base import ChannelAdapter, ContentPack, PublishResult, PerformanceData
from core.database import PVDatabase


class DouyinChannel(ChannelAdapter):
    """抖音渠道适配器
    
    当前版本：导出为可复制发布的Markdown格式
    未来版本：对接抖音开放API或BrowserAct自动发布
    """
    
    CHANNEL_NAME = "douyin"
    
    def __init__(self):
        self.db = PVDatabase()
    
    def publish(self, content_pack: ContentPack) -> PublishResult:
        """导出为抖音发布格式（Markdown + 纯文本）
        
        产出：
        1. 完整标题（含emoji）
        2. 正文（钩子+正文+CTA）
        3. 话题标签建议
        4. 建议发布时间
        """
        try:
            # 生成追踪ID
            tracking_id = content_pack.tracking_id or f"DY_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 生成发布包
            publish_data = self._format_for_douyin(content_pack, tracking_id)
            
            # 保存到data/output/
            output_dir = BASE / "data" / "output" / "douyin"
            output_dir.mkdir(parents=True, exist_ok=True)
            filepath = output_dir / f"{tracking_id}.md"
            filepath.write_text(publish_data, encoding="utf-8")
            
            # 写入content_items表（标记为已发布）
            self.db.save_content_item(tracking_id, self.CHANNEL_NAME, tracking_id=tracking_id, filepath=str(filepath), status="published")
            
            return PublishResult(
                success=True,
                item_id=tracking_id,
                url=str(filepath),
            )
        except Exception as e:
            return PublishResult(success=False, error=str(e))
    
    def _format_for_douyin(self, pack: ContentPack, tracking_id: str) -> str:
        """格式化抖音发布内容"""
        # 标题：最多30字，加emoji
        title_emojis = ["🔥", "⚡", "💡", "📌", "🚀", "💰", "🏠", "☀️"]
        import random
        emoji = random.choice(title_emojis)
        title = f"{emoji}{pack.hook[:28]}"
        
        # 话题标签（根据方向生成）
        tags = self._generate_tags(pack.template_used, pack.industry)
        
        lines = []
        lines.append(f"# 抖音发布包 | {tracking_id}")
        lines.append(f"生成时间: {pack.generated_at}")
        lines.append(f"来源: {pack.source_title if hasattr(pack, 'source_title') else pack.title}")
        lines.append("")
        lines.append("## 标题（30字内）")
        lines.append(title)
        lines.append("")
        lines.append("## 正文（可直接复制）")
        lines.append(pack.hook)
        lines.append("")
        lines.append(pack.body)
        lines.append("")
        lines.append(pack.cta)
        lines.append("")
        lines.append("## 话题标签")
        lines.append(" ".join(tags))
        lines.append("")
        lines.append("## 建议")
        lines.append(f"- 追踪ID: {tracking_id}")
        lines.append(f"- 模板方向: {pack.template_used}")
        lines.append(f"- 行业: {pack.industry}")
        lines.append("- 最佳发布时间: 工作日 12:00-13:00 或 18:00-20:00")
        
        return "\n".join(lines)
    
    def _generate_tags(self, direction: str, industry: str) -> List[str]:
        """根据方向生成话题标签"""
        tag_map = {
            "policy": ["#光伏政策", "#屋顶光伏", "#分布式光伏"],
            "benefit": ["#光伏收益", "#光伏发电", "#投资回报"],
            "avoid": ["#光伏避坑", "#光伏安装", "#业主必看"],
            "news": ["#光伏新闻", "#行业趋势", "#光伏装机"],
            "tech": ["#光伏技术", "#太阳能发电", "#科普"],
        }
        tags = tag_map.get(direction, tag_map["news"])
        tags += [f"#{industry}", "#新能源", "#碳中和"]
        return list(set(tags))[:12]
    
    def get_performance(self, item_id: str) -> PerformanceData:
        """查询效果数据（待对接API）"""
        return PerformanceData()
    
    def collect_leads(self) -> List[Dict]:
        """收集线索（待对接API）"""
        return []


if __name__ == "__main__":
    print("Douyin channel adapter loaded")
