# -*- coding: utf-8 -*-
"""头条/今日头条渠道适配器 - 导出格式（无API版）"""
import sys, os, random
from pathlib import Path
from typing import List, Dict
from datetime import datetime

BASE = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))

from core.channel.base import ChannelAdapter, ContentPack, PublishResult, PerformanceData
from core.database import PVDatabase


class ToutiaoChannel(ChannelAdapter):
    """头条渠道适配器
    
    当前版本：导出为头条图文发布格式
    未来版本：对接头条号开放API
    """
    
    CHANNEL_NAME = "toutiao"
    
    def __init__(self):
        self.db = PVDatabase()
    
    def publish(self, content_pack: ContentPack) -> PublishResult:
        try:
            tracking_id = content_pack.tracking_id or f"TT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            publish_data = self._format_for_toutiao(content_pack, tracking_id)
            
            output_dir = BASE / "data" / "output" / "toutiao"
            output_dir.mkdir(parents=True, exist_ok=True)
            filepath = output_dir / f"{tracking_id}.md"
            filepath.write_text(publish_data, encoding="utf-8")
            
            self.db.save_content_item(tracking_id, self.CHANNEL_NAME, tracking_id=tracking_id, filepath=str(filepath), status="published")
            
            return PublishResult(success=True, item_id=tracking_id, url=str(filepath))
        except Exception as e:
            return PublishResult(success=False, error=str(e))
    
    def _format_for_toutiao(self, pack: ContentPack, tracking_id: str) -> str:
        """格式化头条发布内容"""
        # 标题：头条标题20-30字效果好，加数字或问句
        title = f"{pack.hook[:28]}"
        if not any(c in title for c in ["？", "?", "！"]):
            title = f"{title}，你知道吗？"
        
        lines = []
        lines.append(f"# 头条发布包 | {tracking_id}")
        lines.append(f"生成时间: {pack.generated_at}")
        lines.append(f"来源: {getattr(pack, 'source_title', pack.title)}")
        lines.append("")
        lines.append("## 标题（20-30字）")
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
        tags = self._generate_tags(getattr(pack, 'template_used', 'news'), getattr(pack, 'industry', 'solar'))
        lines.append(" ".join(tags))
        lines.append("")
        lines.append("## 建议")
        lines.append(f"- 追踪ID: {tracking_id}")
        lines.append(f"- 模板方向: {getattr(pack, 'template_used', 'news')}")
        lines.append(f"- 行业: {getattr(pack, 'industry', 'solar')}")
        lines.append("- 最佳发布时间: 工作日 7:00-8:00 或 12:00-13:00 或 20:00-21:00")
        lines.append("- 头条用户偏好：实用干货 > 情绪渲染")
        
        return "\n".join(lines)
    
    def _generate_tags(self, direction: str, industry: str) -> List[str]:
        tag_map = {
            "policy": ["光伏政策", "屋顶光伏", "分布式光伏", "新能源政策"],
            "benefit": ["光伏收益", "光伏发电", "投资回报", "省电省钱"],
            "avoid": ["光伏避坑", "光伏安装", "业主必看", "光伏陷阱"],
            "news": ["光伏新闻", "行业趋势", "光伏装机", "新能源"],
            "tech": ["光伏技术", "太阳能发电", "科普", "清洁能源"],
        }
        tags = tag_map.get(direction, tag_map["news"])
        tags += [industry, "碳中和", "绿色能源"]
        return list(set(tags))[:12]
    
    def get_performance(self, item_id: str) -> PerformanceData:
        return PerformanceData()
    
    def collect_leads(self) -> List[Dict]:
        return []


if __name__ == "__main__":
    print("Toutiao channel adapter loaded")
