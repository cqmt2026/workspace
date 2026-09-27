# -*- coding: utf-8 -*-
"""渠道统一接口定义"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class ContentPack:
    """内容发布包"""
    title: str
    hook: str
    body: str
    cta: str
    channel: str
    industry: str
    template_used: str
    tracking_id: str
    media_files: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

@dataclass
class PublishResult:
    """发布结果"""
    success: bool
    item_id: Optional[str] = None
    error: Optional[str] = None
    url: Optional[str] = None

@dataclass
class PerformanceData:
    """效果数据"""
    plays: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    leads: int = 0

class ChannelAdapter(ABC):
    """渠道统一接口，所有渠道必须实现"""
    
    @abstractmethod
    def publish(self, content_pack: ContentPack) -> PublishResult:
        """发布内容"""
        pass
    
    @abstractmethod
    def get_performance(self, item_id: str) -> PerformanceData:
        """查询效果数据"""
        pass
    
    @abstractmethod
    def collect_leads(self) -> List[Dict]:
        """收集线索（评论/私信/表单）"""
        pass

if __name__ == "__main__":
    print("Channel adapter interface loaded")
