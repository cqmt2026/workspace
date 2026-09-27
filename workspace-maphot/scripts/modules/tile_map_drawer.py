# -*- coding: utf-8 -*-
"""
TileMapDrawer - 高德瓦片地图绘制器（v2 热力图+飞线版）
使用高德地图瓦片作为底图，在真实地图上标注点位
注册为"实景地图"地图形式，可被MapMgr调用

功能：
- 基础点位标注（名称+类型+颜色）
- 热力图叠加（gaussian_kde密度图）
- 飞线/路径图（两点之间连线）
- 柱状图面板
- 图例

用法:
    drawer = TileMapDrawer(style="default")
    result = drawer.draw(segment, output_dir, index=0, total=1)

    # 直接调用:
    drawer.draw_points(points=[{name, lon, lat, type}], output_path="map.png", title="...")
    drawer.draw_heatmap(points=[...], output_path="heatmap.png", title="...")
    drawer.draw_flow(points=[...], connections=[(0,1), (2,3)], output_path="flow.png")
"""

import os
import math
import json
import logging
import urllib.request
import numpy as np
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 高德地图瓦片URL
AMAP_URL = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style={style}&x={x}&y={y}&z={z}"

# 点位类型颜色
POINT_COLORS = {
    "历史遗址": "#E74C3C",
    "文化空间": "#3498DB",
    "火锅餐饮": "#E67E22",
    "主题景区": "#9B59B6",
    "纳凉点": "#2ECC71",
    "默认": "#FFFFFF",
}


# =============================================================================
# 瓦片工具函数
# =============================================================================

def latlon_to_tile(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile


def tile_to_latlon(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat = math.degrees(lat_rad)
    return lat, lon


def fetch_tile(xtile, ytile, zoom, style=8):
    url = AMAP_URL.format(style=style, x=xtile, y=ytile, z=zoom)
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        resp = urllib.request.urlopen(req, timeout=10)
        from PIL import Image
        return Image.open(BytesIO(resp.read())).convert('RGBA')
    except Exception as e:
        logger.warning(f"瓦片下载失败 ({zoom}/{xtile}/{ytile}): {e}")
        from PIL import Image
        return Image.new('RGBA', (256, 256), (240, 240, 240, 255))


def fetch_tile_grid(lat_min, lon_min, lat_max, lon_max, zoom, style=8):
    xtile_min, ytile_north = latlon_to_tile(lat_max, lon_min, zoom)
    xtile_max, ytile_south = latlon_to_tile(lat_min, lon_max, zoom)
    if ytile_north > ytile_south:
        ytile_north, ytile_south = ytile_south, ytile_north

    tiles = {}
    for xtile in range(xtile_min, xtile_max + 1):
        for ytile in range(ytile_north, ytile_south + 1):
            tiles[(xtile, ytile)] = fetch_tile(xtile, ytile, zoom, style)

    lat_north, lon_west = tile_to_latlon(xtile_min, ytile_north, zoom)
    lat_south, lon_east = tile_to_latlon(xtile_max + 1, ytile_south + 1, zoom)
    return tiles, (lon_west, lon_east, lat_south, lat_north), (xtile_min, ytile_north, xtile_max, ytile_south)


def _setup_chinese_font():
    """设置matplotlib中文字体"""
    import matplotlib
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt
    fm.fontManager.addfont('C:/Windows/Fonts/msyhbd.ttc')
    plt.rcParams['font.family'] = 'Microsoft YaHei'
    plt.rcParams['axes.unicode_minus'] = False
    return plt


# =============================================================================
# TileMapDrawer
# =============================================================================

class TileMapDrawer:
    """
    高德瓦片地图绘制器
    支持：点位标注、热力图、飞线图、柱状图面板
    """

    def __init__(self, style: str = "default", zoom: int = 12):
        self.style = style
        self.zoom = zoom
        self.tile_style = 8
        self._load_style_config()

    def _load_style_config(self):
        try:
            from .style_config import STYLE_CONFIGS
            self.config = STYLE_CONFIGS.get(self.style, STYLE_CONFIGS.get("default", {}))
        except ImportError:
            self.config = {}

    # =====================================================================
    # 兼容MapMgr接口
    # =====================================================================

    def draw(self, segment, output_dir: str, index: int = 0, total: int = 1):
        """兼容MapMgr的draw接口"""
        bounds = self._parse_bounds(segment.map_instruction if hasattr(segment, 'map_instruction') else '')
        points = []
        if hasattr(segment, 'highlight_data') and segment.highlight_data:
            hd = segment.highlight_data
            if 'lon' in hd and 'lat' in hd:
                points.append({
                    "name": hd.get('name', ''),
                    "lon": hd['lon'], "lat": hd['lat'],
                    "type": hd.get('type', '默认'),
                    "desc": hd.get('desc', ''),
                    "weight": hd.get('weight', 1),
                })

        filename = f"tilemap_{index:03d}.png"
        output_path = os.path.join(output_dir, filename)

        # 判断地图指令类型
        instruction = segment.map_instruction if hasattr(segment, 'map_instruction') else ''
        if '热力' in instruction or 'heat' in instruction.lower():
            result_path = self.draw_heatmap(
                points=points, output_path=output_path, bounds=bounds, zoom=self.zoom,
                title=segment.title if hasattr(segment, 'title') else None,
            )
        elif '飞线' in instruction or 'flow' in instruction.lower() or '连线' in instruction:
            result_path = self.draw_flow(
                points=points, output_path=output_path, bounds=bounds, zoom=self.zoom,
                title=segment.title if hasattr(segment, 'title') else None,
            )
        else:
            result_path = self.draw_points(
                points=points, output_path=output_path, bounds=bounds, zoom=self.zoom,
                title=segment.title if hasattr(segment, 'title') else None,
                subtitle=segment.subtitle if hasattr(segment, 'subtitle') else None,
            )

        from .schemas import MapResult, MapFile, generate_id
        map_file = MapFile(
            filename=filename, path=result_path or output_path,
            map_form="实景地图",
            highlight_province=points[0]['name'] if points else None,
            style=self.style,
            duration_seconds=segment.duration_seconds if hasattr(segment, 'duration_seconds') else 5.0,
            has_transparent_bg=False, dimensions="1080x1920"
        )
        return MapResult(
            id=generate_id("map"),
            segment_id=segment.id if hasattr(segment, 'id') else "",
            map_form="实景地图", style=self.style, output_files=[map_file]
        )

    # =====================================================================
    # 基础底图
    # =====================================================================

    def _get_base_map(self, bounds: tuple, zoom: int):
        """下载并拼接底图，返回 (fig, ax, extent)"""
        lon_min, lon_max, lat_min, lat_max = bounds
        plt = _setup_chinese_font()

        tiles, extent, tile_range = fetch_tile_grid(
            lat_min, lon_min, lat_max, lon_max, zoom, self.tile_style)

        from PIL import Image
        n_tiles_x = tile_range[2] - tile_range[0] + 1
        n_tiles_y = tile_range[3] - tile_range[1] + 1
        mosaic = Image.new('RGBA', (n_tiles_x * 256, n_tiles_y * 256))
        for (xtile, ytile), img in tiles.items():
            x_offset = (xtile - tile_range[0]) * 256
            y_offset = (ytile - tile_range[1]) * 256
            mosaic.paste(img, (x_offset, y_offset))

        WIDTH, HEIGHT = 1080, 1920
        fig = plt.figure(figsize=(WIDTH / 100, HEIGHT / 100), dpi=100)
        ax = fig.add_axes([0, 0, 1, 1], facecolor='#0D0D17')
        ax.imshow(mosaic, extent=extent, alpha=0.85, zorder=1)

        return fig, ax, extent

    def _save_fig(self, fig, output_path):
        """保存并裁剪为1080x1920"""
        import matplotlib.pyplot as plt
        from PIL import Image
        tmp_path = output_path + '.tmp.png'
        fig.savefig(tmp_path, dpi=100, facecolor='#0D0D17',
                    bbox_inches='tight', pad_inches=0)
        plt.close(fig)

        img = Image.open(tmp_path).convert('RGBA')
        w, h = img.size
        target_w, target_h = 1080, 1920
        scale = target_h / h
        new_w = int(w * scale)
        new_h = target_h
        img = img.resize((new_w, new_h), Image.LANCZOS)
        if new_w > target_w:
            left = (new_w - target_w) // 2
            img = img.crop((left, 0, left + target_w, target_h))
        else:
            padded = Image.new('RGBA', (target_w, target_h), (13, 13, 23, 255))
            left = (target_w - new_w) // 2
            padded.paste(img, (left, 0))
            img = padded
        img.save(output_path, 'PNG')
        os.remove(tmp_path)

        size_kb = os.path.getsize(output_path) / 1024
        logger.info(f"地图已保存: {output_path} ({size_kb:.1f}KB)")

    def _auto_bounds(self, points: List[Dict]) -> tuple:
        """自动计算经纬度范围"""
        lons = [p['lon'] for p in points if 'lon' in p]
        lats = [p['lat'] for p in points if 'lat' in p]
        if not lons or not lats:
            return (106.38, 106.68, 29.42, 29.65)
        margin = 0.03
        return (
            max(min(lons) - margin, 105.0),
            min(max(lons) + margin, 110.0),
            max(min(lats) - margin, 28.0),
            min(max(lats) + margin, 31.0),
        )

    def _add_title(self, ax, title: str = None, subtitle: str = None):
        """添加标题"""
        if title:
            ax.text(0.5, 0.97, title, fontsize=28, color='white',
                    ha='center', va='top', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#0D0D17', alpha=0.7, edgecolor='none'),
                    transform=ax.transAxes, zorder=10)
        if subtitle:
            ax.text(0.5, 0.93, subtitle, fontsize=11, color='#CCCCCC', ha='center', va='top',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#0D0D17', alpha=0.6, edgecolor='none'),
                    transform=ax.transAxes, zorder=10)

    # =====================================================================
    # 模式1：点位标注图
    # =====================================================================

    def draw_points(self, points: List[Dict], output_path: str,
                    bounds: tuple = None, title: str = None, subtitle: str = None,
                    zoom: int = None, show_legend: bool = True,
                    show_bar: bool = False, bar_data: Dict = None):
        """在真实地图上标注点位"""
        import matplotlib.patches as mpatches
        zoom = zoom or self.zoom
        bounds = bounds or self._auto_bounds(points)

        fig, ax, extent = self._get_base_map(bounds, zoom)

        # 绘制点位
        for pt in points:
            name = pt.get('name', '')
            lon = pt.get('lon', 0)
            lat = pt.get('lat', 0)
            ptype = pt.get('type', '默认')
            color = POINT_COLORS.get(ptype, POINT_COLORS['默认'])

            ax.scatter(lon, lat, s=800, c=color, alpha=0.12, edgecolors='none', zorder=5)
            ax.scatter(lon, lat, s=350, c=color, alpha=0.25, edgecolors='none', zorder=6)
            ax.scatter(lon, lat, s=90, c=color, edgecolors='white', linewidth=2, zorder=7)
            ax.text(lon, lat + 0.012, name, fontsize=9, color='white',
                    ha='center', va='bottom', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.25', facecolor=color, alpha=0.85,
                              edgecolor='white', linewidth=0.5), zorder=8)

        # 图例
        if show_legend and points:
            used_types = set(p.get('type', '默认') for p in points)
            legend_elements = [mpatches.Patch(color=POINT_COLORS.get(t, '#FFFFFF'), label=t, alpha=0.8)
                               for t in sorted(used_types)]
            if legend_elements:
                ax.legend(handles=legend_elements, loc='lower left',
                          fontsize=8, framealpha=0.85,
                          facecolor='#1A1A2E', edgecolor='#3A3A5E', labelcolor='white')

        # 柱状图
        if show_bar and bar_data:
            panel_ax = fig.add_axes([0.60, 0.07, 0.35, 0.32], facecolor='#1A1A2E')
            panel_ax.set_facecolor('#1A1A2E')
            sorted_data = sorted(bar_data.items(), key=lambda x: x[1], reverse=True)
            names = [d[0][:2] for d in sorted_data]
            values = [d[1] for d in sorted_data]
            colors_bar = ['#E74C3C' if v >= 10 else '#3498DB' if v >= 5 else '#2ECC71' for v in values]
            bars = panel_ax.barh(range(len(names)), values, color=colors_bar, height=0.6, alpha=0.9)
            panel_ax.set_yticks(range(len(names)))
            panel_ax.set_yticklabels(names, fontsize=8, color='#CCCCCC')
            panel_ax.set_xlim(0, max(values) + 3)
            panel_ax.invert_yaxis()
            for i, (bar, v) in enumerate(zip(bars, values)):
                panel_ax.text(v + 0.3, i, str(v), fontsize=9, color='white', va='center', fontweight='bold')
            panel_ax.set_title("数据分布", fontsize=10, color='white', fontweight='bold', pad=8)
            for spine in panel_ax.spines.values():
                spine.set_visible(False)
            panel_ax.tick_params(colors='#AAAAAA', labelsize=8)
            panel_ax.patch.set_alpha(0.85)

        self._add_title(ax, title, subtitle)
        ax.text(0.5, 0.02, "底图: 高德地图", fontsize=8, color='#888888',
                ha='center', va='bottom', transform=ax.transAxes, zorder=10)
        ax.set_xlim(bounds[0], bounds[1])
        ax.set_ylim(bounds[2], bounds[3])
        ax.set_axis_off()
        self._save_fig(fig, output_path)
        return output_path

    # =====================================================================
    # 模式2：热力图
    # =====================================================================

    def draw_heatmap(self, points: List[Dict], output_path: str,
                     bounds: tuple = None, title: str = None, zoom: int = None):
        """
        在真实地图上叠加热力图
        points 支持 weight 字段控制密度权重
        """
        zoom = zoom or self.zoom
        bounds = bounds or self._auto_bounds(points)

        fig, ax, extent = self._get_base_map(bounds, zoom)

        # 提取坐标和权重
        lons = np.array([p['lon'] for p in points if 'lon' in p])
        lats = np.array([p['lat'] for p in points if 'lat' in p])
        weights = np.array([p.get('weight', 1) for p in points if 'lon' in p])

        if len(lons) >= 3:
            # 用纯numpy实现简单KDE（避免scipy版本冲突）
            def simple_kde(xs, ys, x_grid, y_grid, bandwidth=0.02):
                zi = np.zeros_like(x_grid, dtype=float)
                for x, y, w in zip(lons, lats, weights):
                    dist_sq = (x_grid - x) ** 2 + (y_grid - y) ** 2
                    zi += w * np.exp(-dist_sq / (2 * bandwidth ** 2))
                zi = zi / zi.max() if zi.max() > 0 else zi
                return zi

            xi = np.linspace(bounds[0], bounds[1], 150)
            yi = np.linspace(bounds[2], bounds[3], 150)
            xi_grid, yi_grid = np.meshgrid(xi, yi)
            zi = simple_kde(xi, yi, xi_grid, yi_grid, bandwidth=0.02)

            # 热力图叠加（从红到黄渐变）
            from matplotlib.colors import LinearSegmentedColormap
            heat_colors = [(0, 0, 0, 0), (1, 0, 0, 0.1), (1, 0.5, 0, 0.3), (1, 1, 0, 0.5)]
            cmap = LinearSegmentedColormap.from_list('heat', heat_colors, N=256)
            ax.contourf(xi_grid, yi_grid, zi, levels=20, cmap=cmap, alpha=0.6, zorder=3)
            ax.contour(xi_grid, yi_grid, zi, levels=5, colors='white', linewidths=0.3, alpha=0.3, zorder=4)

        # 标注点位
        for pt in points:
            lon, lat = pt.get('lon', 0), pt.get('lat', 0)
            ptype = pt.get('type', '默认')
            color = POINT_COLORS.get(ptype, POINT_COLORS['默认'])
            ax.scatter(lon, lat, s=60, c=color, edgecolors='white', linewidth=1, zorder=7)

        self._add_title(ax, title, "热力图 | 颜色越亮密度越高")
        ax.set_xlim(bounds[0], bounds[1])
        ax.set_ylim(bounds[2], bounds[3])
        ax.set_axis_off()
        self._save_fig(fig, output_path)
        return output_path

    # =====================================================================
    # 模式3：飞线/路径图
    # =====================================================================

    def draw_flow(self, points: List[Dict], output_path: str,
                  connections: List[Tuple[int, int]] = None,
                  bounds: tuple = None, title: str = None, zoom: int = None):
        """
        在地图上绘制飞线/路径连线
        connections: [(from_idx, to_idx), ...] 连接points中的索引
        """
        import matplotlib.patches as mpatches
        zoom = zoom or self.zoom
        bounds = bounds or self._auto_bounds(points)

        fig, ax, extent = self._get_base_map(bounds, zoom)

        # 自动生成连接（如果没提供，按顺序连接）
        if connections is None and len(points) >= 2:
            connections = [(i, i + 1) for i in range(len(points) - 1)]

        # 绘制飞线
        if connections:
            for from_idx, to_idx in connections:
                if from_idx >= len(points) or to_idx >= len(points):
                    continue
                p1 = points[from_idx]
                p2 = points[to_idx]
                x1, y1 = p1['lon'], p1['lat']
                x2, y2 = p2['lon'], p2['lat']

                # 贝塞尔曲线控制点（向上弯曲）
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2 + (abs(x2 - x1) + abs(y2 - y1)) * 0.15

                # 绘制曲线
                t = np.linspace(0, 1, 100)
                bx = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t ** 2 * x2
                by = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t ** 2 * y2
                ax.plot(bx, by, color='#FFD700', linewidth=1.5, alpha=0.6, zorder=4)

                # 箭头（终点）
                dx = bx[-1] - bx[-2]
                dy = by[-1] - by[-2]
                angle = math.degrees(math.atan2(dy, dx))
                ax.scatter(x2, y2, s=50, c='#FFD700', edgecolors='white', linewidth=1, zorder=6, marker='>',
                           transform=ax.transData)

        # 标注点位
        for i, pt in enumerate(points):
            lon, lat = pt.get('lon', 0), pt.get('lat', 0)
            name = pt.get('name', f'P{i}')
            ptype = pt.get('type', '默认')
            color = POINT_COLORS.get(ptype, POINT_COLORS['默认'])
            ax.scatter(lon, lat, s=80, c=color, edgecolors='white', linewidth=2, zorder=7)
            ax.text(lon, lat + 0.012, name, fontsize=8, color='white',
                    ha='center', va='bottom', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor=color, alpha=0.8, edgecolor='none'), zorder=8)

        self._add_title(ax, title, "路径连线图")
        ax.set_xlim(bounds[0], bounds[1])
        ax.set_ylim(bounds[2], bounds[3])
        ax.set_axis_off()
        self._save_fig(fig, output_path)
        return output_path

    # =====================================================================
    # 辅助
    # =====================================================================

    def _parse_bounds(self, instruction: str) -> tuple:
        if not instruction:
            return (106.38, 106.68, 29.42, 29.65)
        inst = instruction.lower()
        if '重庆' in inst:
            return (106.38, 106.68, 29.42, 29.65) if '主城' not in inst else (106.45, 106.60, 29.53, 29.58)
        if '成都' in inst:
            return (103.90, 104.20, 30.55, 30.75)
        if '北京' in inst:
            return (116.20, 116.55, 39.80, 40.05)
        if '上海' in inst:
            return (121.30, 121.60, 31.10, 31.35)
        if '深圳' in inst:
            return (113.80, 114.30, 22.45, 22.65)
        if '广州' in inst:
            return (113.15, 113.55, 22.95, 23.20)
        return (106.38, 106.68, 29.42, 29.65)


# =============================================================================
# 注册
# =============================================================================

def register():
    try:
        from .map_mgr import register_drawer
        register_drawer("实景地图", TileMapDrawer)
        logger.info("TileMapDrawer v2 已注册为 '实景地图'")
    except Exception as e:
        logger.warning(f"注册TileMapDrawer失败: {e}")


if __name__ != '__main__':
    register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    drawer = TileMapDrawer()
    output_dir = os.path.join(BASE_DIR, 'data', 'maps', datetime.now().strftime("%Y%m%d"))
    os.makedirs(output_dir, exist_ok=True)

    points = [
        {"name": "十八梯大隧道遗址", "lon": 106.573469, "lat": 29.552486, "type": "历史遗址", "weight": 5},
        {"name": "军哥书屋", "lon": 106.541, "lat": 29.503, "type": "文化空间", "weight": 3},
        {"name": "地下之城老火锅", "lon": 106.557, "lat": 29.586, "type": "火锅餐饮", "weight": 4},
        {"name": "洞舰1号", "lon": 106.479714, "lat": 29.553502, "type": "主题景区", "weight": 3},
        {"name": "大龙山纳凉点", "lon": 106.548, "lat": 29.599, "type": "纳凉点", "weight": 2},
        {"name": "黄葛古道防空洞", "lon": 106.614, "lat": 29.542, "type": "历史遗址", "weight": 2},
        {"name": "三峡广场纳凉点", "lon": 106.457, "lat": 29.557, "type": "纳凉点", "weight": 2},
        {"name": "铁路五村防空洞群", "lon": 106.543, "lat": 29.501, "type": "文化空间", "weight": 3},
    ]

    # 测试1：热力图
    print("绘制热力图...")
    drawer.draw_heatmap(
        points=points,
        output_path=os.path.join(output_dir, "tilemap_heatmap.png"),
        title="重庆防空洞热力图",
    )

    # 测试2：飞线图
    print("绘制飞线图...")
    drawer.draw_flow(
        points=points,
        output_path=os.path.join(output_dir, "tilemap_flow.png"),
        title="重庆防空洞游览路线",
        connections=[(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)],
    )

    # 测试3：点位标注图
    print("绘制点位标注图...")
    drawer.draw_points(
        points=points,
        output_path=os.path.join(output_dir, "tilemap_points.png"),
        title="重庆防空洞游玩地图",
        subtitle="中心城区1600+防空洞 | 44处纳凉点免费开放",
        show_legend=True,
        show_bar=True,
        bar_data={"渝中区": 10, "沙坪坝区": 11, "江北区": 6, "南岸区": 4,
                  "渝北区": 2, "大渡口区": 2, "巴南区": 2, "北碚区": 1},
    )

    print("\n全部完成!")