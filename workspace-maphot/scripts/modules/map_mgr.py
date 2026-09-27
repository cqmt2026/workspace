# -*- coding: utf-8 -*-
"""
地图管理器 MapMgr
工厂模式 + 注册表 + 风格配置
职责:根据地图形式和风格,选择对应的绘制器并生成地图
"""

import os
import logging
from typing import Dict, List, Optional, Type, Any
from datetime import datetime

from .schemas import MapResult, MapFile, ScriptSegment, generate_id

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# 1. 绘制器基类
# =============================================================================

class BaseDrawer:
    """绘制器基类,所有地图绘制器继承此类"""

    name = ""  # 地图形式名称,子类覆盖

    def __init__(self, style: str = "default"):
        self.style = style
        self._load_style_config()

    def _load_style_config(self):
        """加载风格配置,子类可覆盖"""
        from .style_config import STYLE_CONFIGS
        self.config = STYLE_CONFIGS.get(self.style, STYLE_CONFIGS.get("default", {}))

    def draw(self, segment: ScriptSegment, output_dir: str,
             index: int = 0, total: int = 1) -> MapResult:
        """
        绘制单张地图

        Args:
            segment: 脚本段落(含地图指令和高亮数据)
            output_dir: 输出目录
            index: 当前段落序号(用于文件名)
            total: 总段落数

        Returns:
            MapResult: 地图结果
        """
        raise NotImplementedError("子类必须实现 draw 方法")


# =============================================================================
# 2. 全国俯瞰图绘制器
# =============================================================================

class NationalOverviewDrawer(BaseDrawer):
    """全国俯瞰图 - 展示全国全貌"""

    name = "全国俯瞰图"

    def draw(self, segment: ScriptSegment, output_dir: str,
             index: int = 0, total: int = 1) -> MapResult:
        """绘制全国俯瞰图"""
        from .province_map_drawer import ProvinceMapDrawer

        drawer = ProvinceMapDrawer(style=self.style)
        filename = f"overview_{index:03d}.png"
        output_path = os.path.join(output_dir, filename)

        # 如果有高亮数据，提取高亮省份
        highlight_name = None
        provinces_data = []
        if segment.highlight_data:
            highlight_name = segment.highlight_data.get('name')
        # 全部省份数据（用于柱状图面板）
        all_provinces = getattr(segment, 'all_provinces', None) or []
        provinces_data = all_provinces if all_provinces else ([segment.highlight_data] if segment.highlight_data else [])

        # 调用现有绘制器
        result_path = drawer.draw_province_map(
            provinces_data=provinces_data,
            highlight_name=highlight_name,
            output_path=output_path,
            data_label=segment.highlight_data.get('value', '') if segment.highlight_data else None,
            transparent_bg=False,
            map_title=segment.title if getattr(segment, 'title', None) else None,
            map_subtitle=segment.subtitle if getattr(segment, 'subtitle', None) else None
        )

        map_file = MapFile(
            filename=filename,
            path=result_path or output_path,
            map_form=self.name,
            highlight_province=highlight_name,
            style=self.style,
            duration_seconds=segment.duration_seconds,
            has_transparent_bg=False,
            dimensions="1080x1920"
        )

        return MapResult(
            id=generate_id("map"),
            segment_id=segment.id,
            map_form=self.name,
            style=self.style,
            output_files=[map_file]
        )


# =============================================================================
# 3. 区域高亮图绘制器
# =============================================================================

class ProvinceHighlightDrawer(BaseDrawer):
    """区域高亮图 - 高亮指定省份,其他暗色"""

    name = "区域高亮图"

    def draw(self, segment: ScriptSegment, output_dir: str,
             index: int = 0, total: int = 1) -> MapResult:
        """绘制区域高亮图"""
        from .province_map_drawer import ProvinceMapDrawer

        drawer = ProvinceMapDrawer(style=self.style)
        highlight_name = None
        provinces_data = []

        if segment.highlight_data:
            highlight_name = segment.highlight_data.get('name')
        # 全部省份数据（用于柱状图面板）
        all_provinces = getattr(segment, 'all_provinces', None) or []
        provinces_data = all_provinces if all_provinces else ([segment.highlight_data] if segment.highlight_data else [])

        filename = f"highlight_{index:03d}.png"
        output_path = os.path.join(output_dir, filename)

        # 先用非透明背景绘制(含高亮+标题+数据卡片)
        result_path = drawer.draw_province_map(
            provinces_data=provinces_data,
            highlight_name=highlight_name,
            output_path=output_path,
            data_label=segment.highlight_data.get('value', '') if segment.highlight_data else None,
            transparent_bg=False,
            map_title=segment.title if getattr(segment, 'title', None) else None,
            map_subtitle=segment.subtitle if getattr(segment, 'subtitle', None) else None
        )

        map_file = MapFile(
            filename=filename,
            path=result_path or output_path,
            map_form=self.name,
            highlight_province=highlight_name,
            style=self.style,
            duration_seconds=segment.duration_seconds,
            has_transparent_bg=False,
            dimensions="1080x1920"
        )

        return MapResult(
            id=generate_id("map"),
            segment_id=segment.id,
            map_form=self.name,
            style=self.style,
            output_files=[map_file]
        )


# =============================================================================
# 4. 绘制器注册表
# =============================================================================

# 注册表:地图形式名 → 绘制器类
DRAWER_REGISTRY: Dict[str, Any] = {
    "全国俯瞰图": NationalOverviewDrawer,
    "区域高亮图": ProvinceHighlightDrawer,
    "对比并排图": None,  # 延迟导入，避免循环引用
    "实景排名图": None,  # 延迟导入 TileProvinceDrawer
}

# 已注册的绘制器实例缓存
_drawer_instances: Dict[str, BaseDrawer] = {}


def register_drawer(name: str, drawer_class: Type[BaseDrawer]):
    """注册新的地图绘制器"""
    DRAWER_REGISTRY[name] = drawer_class
    logger.info(f"地图绘制器已注册: {name}")


def get_drawer(name: str, style: str = "default") -> Optional[BaseDrawer]:
    """获取绘制器实例(缓存复用)"""
    cache_key = f"{name}_{style}"
    if cache_key in _drawer_instances:
        return _drawer_instances[cache_key]

    cls = DRAWER_REGISTRY.get(name)
    if cls is None:
        # 尝试延迟导入
        try:
            if name == "对比并排图":
                from .compare_drawer import CompareDrawer
                DRAWER_REGISTRY["对比并排图"] = CompareDrawer
                cls = CompareDrawer
            elif name == "地形剖面图":
                from .profile_drawer import ProfileDrawer
                DRAWER_REGISTRY["地形剖面图"] = ProfileDrawer
                cls = ProfileDrawer
            elif name == "实景排名图":
                from .tile_province_drawer import TileProvinceDrawer
                DRAWER_REGISTRY["实景排名图"] = TileProvinceDrawer
                cls = TileProvinceDrawer
        except ImportError as e:
            logger.warning(f"延迟导入失败: {name} - {e}")
        
        if cls is None:
            logger.warning(f"未找到绘制器: {name}, 可用: {list(DRAWER_REGISTRY.keys())}")
            return None

    instance = cls(style=style)
    _drawer_instances[cache_key] = instance
    return instance


# =============================================================================
# 5. MapMgr 主入口
# =============================================================================

class MapMgr:
    """地图管理器 - 统一入口"""

    def __init__(self, style: str = "default", output_dir: str = None,
                 video_title: str = None, video_subtitle: str = None):
        self.style = style
        self.video_title = video_title
        self.video_subtitle = video_subtitle
        if output_dir is None:
            date_str = datetime.now().strftime("%Y%m%d")
            self.output_dir = os.path.join(BASE_DIR, 'data', 'maps', date_str)
        else:
            self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def draw_segment(self, segment: ScriptSegment, index: int = 0,
                     total: int = 1) -> Optional[MapResult]:
        """
        根据段落的地图指令,自动选择绘制器并生成地图

        Args:
            segment: 脚本段落(含 map_instruction 和 highlight_data)
            index: 段落序号
            total: 总段落数

        Returns:
            MapResult 或 None(绘制失败时)
        """
        # 从 map_instruction 中提取地图形式
        map_form = self._parse_map_form(segment.map_instruction)
        if not map_form:
            logger.warning(f"段落 {segment.id} 未指定地图形式,跳过")
            return None

        drawer = get_drawer(map_form, self.style)
        if drawer is None:
            logger.warning(f"段落 {segment.id} 的地图形式 {map_form} 未注册,跳过")
            return None

        logger.info(f"绘制地图: {map_form} | 段落: {segment.id} | 高亮: {segment.highlight_data.get('name', '无') if segment.highlight_data else '无'}")
        return drawer.draw(segment, self.output_dir, index, total)

    def draw_all(self, segments: List[ScriptSegment]) -> List[MapResult]:
        """
        批量绘制所有段落的地图

        Args:
            segments: 脚本段落列表

        Returns:
            List[MapResult]: 地图结果列表
        """
        results = []
        total = len(segments)
        for i, seg in enumerate(segments):
            result = self.draw_segment(seg, i, total)
            if result:
                results.append(result)
                seg.map_result = result
        return results

    def _parse_map_form(self, instruction: str) -> Optional[str]:
        """从自然语言指令中解析地图形式"""
        if not instruction:
            return None

        # 精确匹配
        for form_name in DRAWER_REGISTRY.keys():
            if form_name in instruction:
                return form_name

        # 模糊匹配
        instruction_lower = instruction.lower()
        if '全国' in instruction_lower or '全貌' in instruction_lower or '整体' in instruction_lower:
            return "全国俯瞰图"
        if '对比' in instruction_lower or 'vs' in instruction_lower or '比较' in instruction_lower or '并排' in instruction_lower:
            return "对比并排图"
        if '高亮' in instruction_lower or '聚焦' in instruction_lower or '区域' in instruction_lower:
            return "区域高亮图"

        # 默认
        return "区域高亮图"

    def set_output_dir(self, output_dir: str):
        """设置输出目录"""
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)


# =============================================================================
# 6. 快速测试
# =============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # 测试注册表
    print(f"已注册的绘制器: {list(DRAWER_REGISTRY.keys())}")

    # 测试解析
    mgr = MapMgr()
    test_seg = ScriptSegment(
        id="seg_001",
        technique="反差切入",
        text="中国最热的城市,夏天居然要开空调77天?",
        map_instruction="全国俯瞰图,全图展示",
        duration_seconds=8
    )
    print(f"解析结果: {mgr._parse_map_form(test_seg.map_instruction)}")

    print("MapMgr 初始化成功 ✅")