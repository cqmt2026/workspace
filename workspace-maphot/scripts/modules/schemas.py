# -*- coding: utf-8 -*-
"""
标准化数据接口（Schema）
所有模块通过标准化数据类交换信息，不直接依赖对方内部实现
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os


# =============================================================================
# 1. 选题输出 TopicResult
# =============================================================================

@dataclass
class TopicResult:
    """选题模块输出"""
    id: str                                    # 选题ID
    title: str                                 # 选题标题
    category: str = "一张图"                    # 一张图 / 追热点 / 深一度
    source: str = ""                           # 选题来源
    hotness: int = 0                           # 热度值
    
    # 选题基因分析（匹配矩阵用）
    content_type: str = ""                     # 排名型 / 机制型 / 对比型 / 种草型 / 叙事型
    emotion: str = ""                          # 反差 / 悬念 / 共鸣 / 震撼 / 实用
    data_density: str = "中"                   # 高 / 中 / 低
    timeliness: bool = False                   # 是否有时效性
    
    # 匹配矩阵推荐方案
    recommend: Dict[str, Any] = field(default_factory=dict)
    
    # 原始数据（传给脚本模块）
    raw_data: List[Dict[str, Any]] = field(default_factory=list)
    
    # 元信息
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TopicResult':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# =============================================================================
# 2. 脚本输出 ScriptResult
# =============================================================================

@dataclass
class ScriptSegment:
    """脚本段落"""
    id: str                                    # 段落ID
    technique: str = ""                        # 当前段落使用的文案手法
    text: str = ""                             # 口播文案
    map_instruction: str = ""                  # 地图绘制指令（自然语言）
    highlight_data: Optional[Dict[str, Any]] = None  # 当前高亮的数据
    all_provinces: List[Dict[str, Any]] = None  # 全部省份数据（用于柱状图面板）
    duration_seconds: float = 0.0              # 预计时长
    audio_file: Optional[str] = None           # 配音文件路径（配音模块填充）
    map_result: Optional[Any] = None           # 地图结果（地图模块填充）
    title: Optional[str] = None                # 主标题（脚本级标题）
    subtitle: Optional[str] = None             # 副标题（数据来源等）


@dataclass
class ScriptResult:
    """脚本模块输出"""
    id: str                                    # 脚本ID
    topic_id: str                              # 关联选题ID
    title: str                                 # 标题
    category: str = "一张图"                    # 栏目类型
    writing_techniques: List[str] = field(default_factory=list)  # 使用的文案手法列表
    estimated_duration_seconds: float = 0.0    # 总预计时长
    segments: List[ScriptSegment] = field(default_factory=list)  # 段落列表
    
    # 元信息
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['segments'] = [asdict(s) for s in self.segments]
        return d
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @property
    def word_count(self) -> int:
        return sum(len(s.text) for s in self.segments)
    
    @property
    def audio_duration_seconds(self) -> float:
        return sum(s.duration_seconds for s in self.segments)


# =============================================================================
# 3. 地图输出 MapResult
# =============================================================================

@dataclass
class MapFile:
    """单张地图文件"""
    filename: str                              # 文件名
    path: str                                  # 完整路径
    map_form: str = ""                         # 地图形式
    highlight_province: Optional[str] = None   # 高亮省份（如有）
    style: str = "default"                     # 配色风格
    duration_seconds: float = 0.0              # 对应时长
    has_transparent_bg: bool = False           # 是否透明背景
    dimensions: str = "1080x1920"              # 尺寸
    
    @property
    def exists(self) -> bool:
        return os.path.exists(self.path)


@dataclass
class MapResult:
    """地图模块输出"""
    id: str                                    # 地图序列ID
    segment_id: str                            # 关联段落ID
    map_form: str = ""                         # 地图形式
    style: str = "default"                     # 配色风格
    output_files: List[MapFile] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['output_files'] = [asdict(f) for f in self.output_files]
        return d


# =============================================================================
# 4. 视频输出 VideoResult
# =============================================================================

@dataclass
class VideoResult:
    """视频合成模块输出"""
    id: str                                    # 视频ID
    topic_id: str                              # 关联选题ID
    filename: str = ""                         # 文件名
    path: str = ""                             # 完整路径
    duration_seconds: float = 0.0              # 时长
    resolution: str = "1080x1920"              # 分辨率
    bitrate_kbps: int = 2000                   # 码率
    fps: int = 30                              # 帧率
    file_size_mb: float = 0.0                  # 文件大小
    
    # 元信息
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    @property
    def exists(self) -> bool:
        return os.path.exists(self.path) if self.path else False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# 5. 辅助函数
# =============================================================================

def generate_id(prefix: str = "res") -> str:
    """生成唯一ID"""
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def save_result(result, output_dir: str, filename: str = None) -> str:
    """保存任意Result到JSON文件"""
    if filename is None:
        filename = f"{result.__class__.__name__}_{result.id}.json"
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(result.to_json() if hasattr(result, 'to_json') else json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return path